Welcome to Apache Tika  <https://tika.apache.org/>
=================================================

[![license](https://img.shields.io/github/license/apache/tika.svg?maxAge=2592000)](http://www.apache.org/licenses/LICENSE-2.0)
[![Jenkins](https://img.shields.io/jenkins/s/https/ci-builds.apache.org/job/Tika/job/tika-main-jdk17.svg?maxAge=3600)](https://ci-builds.apache.org/job/Tika/job/tika-main-jdk17/)
[![Jenkins tests](https://img.shields.io/jenkins/t/https/ci-builds.apache.org/job/Tika/job/tika-main-jdk17.svg?maxAge=3600)](https://ci-builds.apache.org/job/Tika/job/tika-main-jdk17/lastBuild/testReport/)
[![Maven Central](https://img.shields.io/maven-central/v/org.apache.tika/tika.svg?maxAge=86400)](http://search.maven.org/#search|ga|1|g%3A%22org.apache.tika%22)

Apache Tika(TM) is a toolkit for detecting and extracting metadata and structured text content from various documents using existing parser libraries.

Tika is a project of the [Apache Software Foundation](https://www.apache.org).

Apache Tika, Tika, Apache, the Apache feather logo, and the Apache Tika project logo are trademarks of The Apache Software Foundation.

## IFT3913 – Tâche 2

Nous retenons `org.apache.tika.detect.ZeroSizeFileDetector`, dans le module
`tika-core`, pour augmenter sa suite de tests. Les deux tests originaux de
`ZeroSizeFileDetectorTest` vérifient le type MIME retourné pour un flux vide et un
flux non vide. La classe est courte, sa couverture des branches est incomplète et
un mutant vivant révèle un comportement que les oracles actuels ne vérifient pas.

Les mesures initiales utilisent le code du commit `a2d75c2c1` de `main`, sans
modification des sources ou des tests. La configuration commune est préparée sur
`tache2/setup`, anciennement `tache2/mutation`.

### Environnement et configuration

Les mesures ont été réalisées le 13 octobre 2026 avec OpenJDK 21.0.10, Maven
3.9.12 via le wrapper du dépôt, JUnit Jupiter et Platform 6.1.3, JaCoCo 0.8.15 et
PIT 1.30.0. La compilation cible Java 17.

La configuration PIT de `tika-core/pom.xml` cible exclusivement
`ZeroSizeFileDetector` et deux classes de tests : `ZeroSizeFileDetectorTest`
(deux tests originaux et un test manuel) et `ZeroSizeFileDetector_detect_0_0_Test`
(sept tests IA). Elle fixe
le groupe d'opérateurs `DEFAULTS` et produit les rapports HTML et XML. L'adaptateur
`pitest-junit5-plugin` 1.2.3 est une dépendance du plugin PIT. Malgré son nom,
l'exécution fonctionne avec notre JUnit 6.1.3 : PIT ajoute automatiquement le
launcher 6.1.3, découvre les tests Jupiter et termine avec succès. La version
JUnit existante est conservée.

PIT est lancé explicitement et n'est pas ajouté au cycle Maven habituel. Les versions, les opérateurs
et la classe cible sont identiques pour M0, M1 et M2. Seule la suite disponible
évolue : deux tests pour M0, neuf pour M1 et dix pour M2.

### Couverture initiale et score de mutation M0

Les résultats JaCoCo ci-dessous concernent uniquement l'exécution des deux tests
originaux de `ZeroSizeFileDetectorTest`.

| Métrique | Éléments couverts | Couverture |
|---|---:|---:|
| Instructions | 20/20 | 100 % |
| Branches | 3/4 | 75 % |
| Lignes | 7/7 | 100 % |

La branche manquante correspond à `tis == null`, qui doit retourner
`MediaType.OCTET_STREAM`. Le choix de la classe repose sur cette couverture des
branches incomplète et sur le mutant survivant ; les instructions sont déjà
couvertes à 100 %.

Avec les tests originaux, PIT génère **6 mutants : 5 tués et 1 survivant**.
Le score initial est **M0 = 5/6 × 100 = 83,33 %** ; PIT affiche 83 % après arrondi.
Aucun mutant n'est sans couverture, en dépassement de temps ou en erreur
d'exécution. Aucun mutant n'a été retiré du dénominateur.

Le survivant utilise `VoidMethodCallMutator` pour supprimer `tis.reset()` à la
ligne 40, dans le `finally`. PIT regroupe les trois copies de cet appel produites
par le compilateur en un seul mutant. Les deux tests passent contre ce mutant,
car ils vérifient seulement le type MIME retourné. Pour un flux non vide, le
mutant retourne encore `OCTET_STREAM`, mais laisse le flux avancé d'un octet.
Le programme original rétablit sa position initiale, conformément au contrat de
`Detector`. Cette différence est observable par une lecture ultérieure : le
mutant n'est donc pas équivalent au programme original.

### Reproduire les mesures

Les commandes suivantes utilisent Java 21 et le wrapper Maven du dépôt. Le profil
`chatunitest` reste désactivé pendant les tests et l'analyse de mutation.

Les mesures doivent employer leur suite respective. La branche finale contient
le test manuel : elle ne reproduit donc pas M0 ou M1 en lançant simplement PIT.

| Mesure | État du code et de la configuration | Tests |
|---|---|---:|
| M0 | Setup `1d3155870`, avant les tests IA et le test manuel | 2 |
| M1 | Génération `ee7f0b7ad`, avec le patch PIT archivé dans M1 | 9 |
| M2 | `6152ec4b2` avec le test manuel et la sélection PIT des deux classes | 10 |

Pour retrouver M0 et M1 sans modifier la branche finale, créer des worktrees
isolés depuis la racine du dépôt :

```sh
git worktree add --detach ../tika-m0 1d3155870
git worktree add --detach ../tika-m1 ee7f0b7ad
git -C ../tika-m1 apply "$PWD/tache2/resultats/M1/configuration-PIT.diff"
```

Depuis la racine du worktree correspondant, ou depuis la branche finale pour M2,
préparer le processeur d'annotations puis exécuter les tests du devoir :

```sh
./mvnw -B -ntp -pl tika-annotation-processor -am install -Dspotless.goal=check
./mvnw -B -ntp -pl tika-core clean test -Dtest='ZeroSizeFileDetector*' \
  -Djacoco.append=false -Dspotless.goal=check
./mvnw -B -ntp -pl tika-core org.pitest:pitest-maven:mutationCoverage
```

Le filtre sélectionne les deux, neuf ou dix tests selon l'état du code. JaCoCo
écrit son rapport dans `tika-core/target/site/jacoco/` et PIT dans
`tika-core/target/pit-reports/`. `jacoco.append=false` évite de cumuler une ancienne
mesure. `spotless.goal=check` vérifie le formatage sans réécrire les sources.

Les commandes exactes et les journaux de M1 et M2 sont archivés dans leurs dossiers
respectifs. Les mesures originales utilisaient `reportsDirectory` pour enregistrer
PIT directement hors de `target`. Pour une nouvelle exécution, conserver le dossier
PIT par défaut puis archiver séparément le résultat ; ne pas écraser les preuves.

Pour identifier tous les tests qui tuent chaque mutant, une exécution complémentaire
utilise la matrice complète, avec les mêmes opérateurs :

```sh
./mvnw -B -ntp -pl tika-core org.pitest:pitest-maven:mutationCoverage \
  -DfullMutationMatrix=true "-DreportsDirectory=$PWD/tika-core/target/pit-matrix"
```

Ce mode poursuit les tests après la première détection. Il ne change ni les six
mutants ni leur score. Les rapports standards fournissent la mesure ; les matrices
complètes de M1 et M2 fournissent l'attribution à tous les tests.

Pour vérifier la suite entière de `tika-core`, le processeur d'annotations et les
contrôles d'API et de licence :

```sh
./mvnw -B -ntp -pl tika-core -am clean test \
  -Djacoco.append=false -Dspotless.goal=check
./mvnw -B -ntp -pl tika-core de.thetaphi:forbiddenapis:check de.thetaphi:forbiddenapis:testCheck
./mvnw -B -ntp -N apache-rat:check
```

La suite entière produit une couverture distincte de la couverture ciblée du devoir.
Les deux tests déjà désactivés dans Tika sont `reproduceRandomizedTestFailure` et
`testUndeclaredEntityXML`. Aucun test n'a été désactivé pour ce travail.

### Preuves conservées

Les résultats initiaux sont copiés dans `tache2/resultats/M0/`, hors de `target`,
afin de survivre à `mvn clean` et aux prochaines mesures :

- [Rapport HTML PIT initial](tache2/resultats/M0/pit-reports/index.html).
- [Résultats XML des six mutants](tache2/resultats/M0/pit-reports/mutations.xml).
- [Compteurs JaCoCo bruts](tache2/resultats/M0/jacoco.csv).
- [Journal des tests originaux](tache2/resultats/M0/tests.log).
- [Journal PIT et résolution JUnit](tache2/resultats/M0/pit.log).
- [Empreintes SHA-256 des fichiers archivés](tache2/resultats/M0/SHA256SUMS).

Les journaux conservent les chemins locaux et les commandes de la mesure initiale.
Ces fichiers sont des preuves à conserver ; les prochaines mesures restent dans
`target` jusqu'à leur archivage séparé.

Le POM racine exclut du contrôle d'en-tête de licence uniquement les dossiers
de preuves générées `M0`, `M1`, `M2` et `generation` sous `tache2/resultats/`.
Ces fichiers bruts sont conservés sans ajout d'en-tête. RAT reste actif sur les
sources, les tests, la configuration Maven et le workflow.

### Génération de tests avec ChatUniTest

ChatUniTest 2.1.1 (`chatunitest-maven-plugin`) est déclaré dans le profil Maven
`chatunitest` de `tika-core/pom.xml`. Le modèle est `qwen2.5-coder:3b` (famille
qwen2, 3,1 milliards de paramètres, quantification Q4_K_M), exécuté en local par
Ollama 0.40.3 sur `http://localhost:11434/v1/chat/completions`.

Le plugin accepte seulement une liste fixe de noms de modèles. Nous utilisons donc
l'alias Ollama `code-llama`, créé avec `ollama cp qwen2.5-coder:3b code-llama`.
Les deux noms pointent vers le même fichier de poids
(`sha256-4a188102020e…`). La configuration demande 3 tests par méthode
(`testNumber`), 3 tours de réparation (`maxRounds`) et désactive le parallélisme
(`thread=false`).

Le profil sert uniquement à la génération. `chatunitest-starter` 1.5.0 ajoute
`junit-platform-runner` 1.7.2 (JUnit 4) : avec `-Pchatunitest`, Surefire exécute
0 test. Les tests s'exécutent donc sans ce profil. Ils ont seulement besoin de
`mockito-core` et `mockito-junit-jupiter`, ajoutés en portée `test`.

Commande de génération, depuis la racine du dépôt :

```sh
./mvnw -B -pl tika-core -Pchatunitest chatunitest:class \
  -DselectClass=ZeroSizeFileDetector \
  -Dcheckstyle.skip -Drat.skip -Dforbiddenapis.skip
```

Les options `-D...skip` empêchent les contrôles de bloquer la génération. Elles ne
servent pas pour l'exécution des tests.

#### Résultats bruts

| Exécution | JDK | Tentatives | Tentatives qui compilent | Tests acceptés |
|---|---|---:|---:|---:|
| 1 | 21.0.12 | 9 | 0 | 0 |
| 2 | 17.0.20 | 9 | 0 | 0 |

Chaque exécution produit 3 tests, avec 3 tours chacun. **ChatUniTest n'a accepté
aucun test sur les 18 tentatives** : toutes échouent à la compilation, sauf une
réponse de l'exécution 2 dont le code n'a pas pu être extrait.

Avec le JDK 21, `javac` ajoute des avertissements, car le processeur
d'annotations de Tika déclare `RELEASE_17`. ChatUniTest les envoie au modèle avec
les vraies erreurs. Nous avons relancé sous JDK 17 pour retirer ce bruit. La
commande de l'exécution 2 contenait aussi `-DmaxRounds=5`, sans effet : la valeur
du POM (3) l'emporte.

Erreurs de compilation produites par le modèle :

- imports manquants (`TemporaryResources`, `ByteArrayInputStream`) ;
- appel du constructeur protégé de `TikaInputStream` au lieu de
  `TikaInputStream.get(byte[])` ;
- appel statique de la méthode d'instance `detect` ;
- bibliothèque absente du projet (`org.reflections`) ;
- `when(...).thenReturn(...)` sur `mark` et `reset`, qui retournent `void`.

#### Corrections

Nous retenons la tentative 0, tour 2, de l'exécution 2. Elle contient 7 tests.
Les corrections sont les suivantes :

1. Suppression de 12 lignes `when(tis.mark(1)).thenReturn(0)` et
   `when(tis.reset()).thenReturn(null)`, 2 par test dans 6 tests. Erreur
   corrigée : `'void' type not allowed here`.
2. Spotless, lancé par le build de Tika en mode `apply`, ajoute l'en-tête de
   licence Apache, trie les imports et retire 2 imports inutiles (`InputStream`,
   `ZeroSizeFileDetector`).
3. Checkstyle (`AvoidStarImport`) refuse 4 imports `.*`. Ils deviennent des
   imports explicites, et `import org.mockito.*` est retiré car inutilisé.

En dehors de la correction 1, le corps des tests ne change pas. Le résultat est
`tika-core/src/test/java/org/apache/tika/detect/ZeroSizeFileDetector_detect_0_0_Test.java`.

#### Critique des assertions

- `testDetectWithNonNullInputStream` simule un flux vide (`read()` retourne -1),
  attend `MediaType.EMPTY` et vérifie un appel à `mark(1)`, `read()` et `reset()`.
  Avec les 5 tests suivants, 6 tests sur 7 vérifient `reset()`, l'appel supprimé
  par le mutant survivant de M0.
- `testDetectWithNullInputStream` passe `null` et attend `MediaType.OCTET_STREAM`.
  Il couvre la branche `tis == null`, absente des tests originaux.
- Les 5 autres tests ont le même corps : `read()` retourne 1, le résultat attendu
  est `OCTET_STREAM` et les mêmes appels sont vérifiés. Ils sont redondants. Leurs
  noms (`ReadLimit`, `Reset`, `CloseShield`, `OverrideLength`) annoncent des cas
  qu'ils ne construisent pas.
- Les oracles portent sur des appels de mocks, pas sur la position réelle du flux.
  Les tests originaux utilisent au contraire un vrai `TikaInputStream.get(byte[])`.
  Les mocks de `Metadata` et `ParseContext` ne servent à rien.

La mesure M1 est terminée : les neuf tests tuent les six mutants (100 %).
L'attribution des détections est détaillée ci-dessous.

#### Vérification

Lors de la validation de la génération, les 9 tests (2 originaux, 7 générés)
passaient sans profil ChatUniTest, avec le
JDK 21.0.12, Checkstyle et Spotless en mode `check` :

```sh
./mvnw -B -ntp -pl tika-annotation-processor -am install -DskipTests -Dspotless.goal=check
./mvnw -B -ntp -pl tika-core clean test -Dtest='ZeroSizeFileDetector*' \
  -Dsurefire.failIfNoSpecifiedTests=false -Djacoco.append=false -Dspotless.goal=check
./mvnw -B -ntp -pl tika-core de.thetaphi:forbiddenapis:testCheck
./mvnw -B -ntp -N apache-rat:check
```

Résultat : `Tests run: 9, Failures: 0, Errors: 0`, 0 violation Checkstyle,
0 erreur forbiddenapis, contrôle RAT réussi.

#### Preuves conservées

Les sorties de ChatUniTest sont copiées dans `tache2/resultats/generation/`, sans
modification :

- `run1-jdk21/` et `run2-jdk17/` : commande, journal Maven, code et erreurs de
  compilation de chaque tentative (`error-message/`), prompts et réponses du
  modèle (`history/`).
- `corrections/` : le test brut (`1-brut`), puis après la correction 1
  (`2-sans-stubs-void`), puis après Spotless (`3-apres-spotless`).
- [Journal des 9 tests](tache2/resultats/generation/tests.log).
- [Empreintes SHA-256](tache2/resultats/generation/SHA256SUMS).

Ces fichiers ne contiennent aucun secret : la clé `ollama` est une valeur fictive
exigée par le plugin. Le POM racine exclut aussi `tache2/resultats/generation/**`
du contrôle RAT.

### Comparaison des mesures de mutation M0, M1 et M2

| Mesure | Suite | Mutants | Tués | Survivants | Score |
|---|---|---:|---:|---:|---:|
| M0 | 2 tests originaux | 6 | 5 | 1 | 83,33 % |
| M1 | 2 originaux + 7 IA | 6 | 6 | 0 | 100 % |
| M2 | 2 originaux + 7 IA + 1 manuel | 6 | 6 | 0 | 100 % |

Les trois mesures utilisent PIT 1.30.0, l'adaptateur Jupiter 1.2.3 et `DEFAULTS`.
Les identifiants des mutants (classe, méthode, opérateur et index du bytecode) ont
été comparés : il s'agit exactement des mêmes six mutants. La classe de production
n'a pas été modifiée. Aucune mesure ne contient de mutant sans couverture, en
échec d'exécution ou en dépassement de temps. Aucun mutant n'est retiré du calcul.

M1 améliore le score de 16,67 points. M2 conserve 100 % : le test manuel ajoute un
oracle sur le comportement réel du flux, sans prétendre augmenter le score obtenu
avec les tests IA. La couverture JaCoCo ciblée passe de 20/20 instructions et
3/4 branches pour M0 à 20/20 instructions et 4/4 branches pour M1 et M2.

#### Mutants détectés par les tests IA

La matrice complète M1 confirme les détections suivantes. Les numéros de ligne
réfèrent à la classe `ZeroSizeFileDetector`, qui reste inchangée.

| Ligne | Mutation PIT | Tests IA détecteurs et raison |
|---|---|---|
| 33 | Suppression de la condition sur le flux | Les six tests avec un flux non nul détectent le résultat incorrect pour le flux vide ou l'absence des appels attendus pour les autres flux. |
| 35 | Suppression de `mark(1)` | Les six tests avec un flux non nul vérifient explicitement `mark(1)`. |
| 36 | Suppression de la condition sur la fin du flux | `testDetectWithNonNullInputStream` simule `read() == -1` et attend `MediaType.EMPTY`. |
| 37 | Remplacement du retour `EMPTY` par `null` | Le même test vérifie exactement `MediaType.EMPTY`. |
| 40 | Suppression de `reset()` | Les six tests avec un flux non nul vérifient exactement un appel à `reset()`. |
| 43 | Remplacement du retour `OCTET_STREAM` par `null` | Le test avec un flux `null` et les cinq tests avec `read() == 1` attendent exactement `OCTET_STREAM`. |

Les cinq mutants déjà tués en M0 restent tués. Le gain vient uniquement du mutant
à la ligne 40, qui survivait aux deux tests originaux. Les six tests IA suivants
le tuent, car `verify(tis, times(1)).reset()` échoue si PIT supprime l'appel :

- `testDetectWithNonNullInputStream` ;
- `testDetectWithMarkedInputStream` ;
- `testDetectWithMarkedInputStreamAndReadLimit` ;
- `testDetectWithMarkedInputStreamAndReadLimitAndReset` ;
- `testDetectWithMarkedInputStreamAndReadLimitAndResetAndCloseShield` ;
- `testDetectWithMarkedInputStreamAndReadLimitAndResetAndCloseShieldAndOverrideLength`.

Le rapport standard arrête l'exécution au premier test qui tue un mutant ; le nom
retenu peut varier avec l'ordre des tests. La matrice complète vérifie les six
détections indépendamment de cet ordre. `testDetectWithNullInputStream` couvre la
branche manquante de M0, mais ne tue pas le mutant `reset()`, puisque cette branche
ne lit ni ne réinitialise le flux.

#### Test manuel et apport de son oracle

Le test ajouté manuellement au projet est `testDetectPreservesStreamPosition`, dans
`ZeroSizeFileDetectorTest`. Il utilise un vrai `TikaInputStream`, fermé par un
`try` avec ressources après les assertions.

- **Intention :** vérifier que `detect()` préserve la position et le contenu du
  flux, conformément au contrat de `Detector`.
- **Données :** `"ABC".getBytes(UTF_8)` donne trois octets distincts, `65`, `66` et
  `67`. Le flux est non vide ; si la détection consomme `A` sans revenir en arrière,
  la perte devient observable à la lecture suivante.
- **Oracle :** `detect()` retourne `OCTET_STREAM`, `tis.getPosition()` vaut toujours
  `0L`, puis `tis.readAllBytes()` restitue exactement les octets de `ABC`.
- **Apport :** les tests IA vérifient des appels sur un mock, dont `reset()` ne
  déplace aucun véritable flux. Ce test vérifie l'effet réel de la détection,
  avec une position inchangée et aucun octet perdu. Les deux tests originaux
  employaient déjà de vrais flux, mais vérifiaient seulement le type MIME.

La matrice complète M2 confirme que ce test détecte la suppression de `reset()`.
Il détecte aussi la suppression de `mark(1)` et le remplacement du retour
`OCTET_STREAM` par `null`. Les tests IA tuaient déjà ces mutants : le score reste
6/6. Aucun mutant ne survit avec `DEFAULTS`, mais cela ne constitue pas une preuve
que tous les comportements possibles sont testés.

#### Commandes et preuves M1/M2

Les preuves M1 ont été copiées octet par octet depuis le worktree `ift3913-m1`.
Leurs empreintes ont été vérifiées, ainsi que celles de M0 et des sorties brutes
ChatUniTest. Ces archives sont séparées et ne sont pas réécrites :

| Mesure | Rapport standard | Attribution complète | Journal des tests | Compteurs JaCoCo |
|---|---|---|---|---|
| M1 | [HTML](tache2/resultats/M1/pit-reports/index.html), [XML](tache2/resultats/M1/pit-reports/mutations.xml) | [XML](tache2/resultats/M1/pit-matrix/mutations.xml) | [Journal](tache2/resultats/M1/tests.log) | [CSV](tache2/resultats/M1/jacoco.csv) |
| M2 | [HTML](tache2/resultats/M2/pit-reports/index.html), [XML](tache2/resultats/M2/pit-reports/mutations.xml) | [XML](tache2/resultats/M2/pit-matrix/mutations.xml) | [Journal](tache2/resultats/M2/tests.log) | [CSV](tache2/resultats/M2/jacoco.csv) |

Chaque dossier contient `commandes.txt`, les journaux PIT, `comparaison.json` et
`SHA256SUMS`. M2 contient également les journaux de préparation, de régression et
de contrôles. Ces résultats restent présents après `mvn clean`.

### GitHub Actions et vérifications finales

Le workflow `.github/workflows/tache2.yml` utilise Ubuntu, Temurin Java 21 et le
wrapper Maven. Il prépare le processeur d'annotations, exécute les dix tests avec
`-Dtest='ZeroSizeFileDetector*'`, puis vérifie les API interdites et les licences
avec Apache RAT. Spotless et Checkstyle restent actifs ; le profil ChatUniTest
n'est pas activé. Les déclencheurs sont les pushes vers `main` ou `tache2/**`, les
PR vers `main` et un lancement manuel.

Les dix tests passent localement, sans échec, erreur ou test ignoré. La suite
entière de `tika-core` compte 757 cas, dont 755 exécutés et les deux cas déjà
désactivés mentionnés plus haut. Le processeur d'annotations exécute huit tests.
Il n'y a aucun échec ni erreur. Spotless, Checkstyle, les API interdites (sources
et tests) et RAT passent. Le workflow et ses commandes sont vérifiés localement. Comme cette finalisation n'a pas encore
été commitée ni poussée, ce nouveau workflow n'a pas encore exécuté ces dix tests
sur GitHub ; sa validation distante reste à effectuer après publication. Les
checks existants du dépôt sur `main` ne valident pas les modifications locales.

Lors du contrôle des checks de `6152ec4b2`, `no split packages` réussit et les
builds Java sont encore en cours. Le workflow existant de publication Docker
échoue à l'étape `Login to Docker Hub` avec `Username and password required` ;
cette étape attend les secrets `DOCKERHUB_USER` et `DOCKERHUB_TOKEN` du dépôt.
Ce workflow de publication n'est pas modifié pour le devoir. L'état distant et
le lien vers l'échec sont enregistrés dans `tache2/resultats/M2/github-actions.json`.

### Utilisation de l'IA

Ce travail a été réalisé par **Thierno Diallo et Andy Luemba Nguema**, avec
l'assistance de ChatGPT.

Nous avons principalement utilisé ChatGPT pour nous aider à mieux comprendre les
consignes du professeur, clarifier les objectifs du devoir, identifier les
différentes étapes à suivre et organiser la répartition des tâches entre nous.

ChatGPT nous a également accompagnés dans notre démarche en nous proposant des
explications et des pistes de résolution lorsque nous rencontrions des difficultés.

**La rédaction du présent README a été réalisée avec l'aide de ChatGPT**, à partir
de notre travail, des résultats obtenus et des informations que nous lui avons
fournies.

Nous avons assuré la réalisation du travail, le suivi des différentes étapes et la
vérification des résultats présentés dans ce document. ChatGPT a principalement
servi d'outil d'accompagnement, de compréhension, d'organisation et d'aide à la
rédaction.

Pour la partie ChatUniTest, nous avons aussi utilisé Claude Code (Anthropic) pour
installer l'environnement, lancer la génération, analyser les erreurs de
compilation et rédiger la section correspondante. Les tests viennent de ChatUniTest
et du modèle local `qwen2.5-coder:3b`. Les corrections sont listées plus haut.

L'assistant Codex (OpenAI) a également aidé à configurer PIT, exécuter et analyser
les mesures M0/M1/M2, rédiger le test ajouté manuellement au projet, préparer le
workflow et compléter cette documentation, sous notre coordination. Le test manuel
ne provient pas de ChatUniTest ; son intention, ses données et son oracle sont
expliqués ci-dessus.

M0 et M1 ont été validés ; M2 est mesuré localement. Cette section documente le
travail réalisé et distingue les vérifications locales de la validation GitHub
Actions encore à effectuer, conformément aux
[consignes de la tâche 2](https://github.com/umontreal-diro/IFT3913/blob/2026/tache2/readme.md)
et aux [instructions de déclaration de l'IA de l'Université de Montréal](https://boite-outils.bib.umontreal.ca/c.php?g=743753&p=5377614).

Quick Start
===========

**Parse a file in Java:**

```java
import org.apache.tika.Tika;

Tika tika = new Tika();
String text = tika.parseToString(new File("document.pdf"));
System.out.println(text);
```

**From the command line:**

```bash
java -jar tika-app-*.jar --text document.pdf
```

**Maven dependency:**

```xml
<dependency>
    <groupId>org.apache.tika</groupId>
    <artifactId>tika-parsers-standard-package</artifactId>
    <version>4.x.y</version>
    <type>pom</type>
</dependency>
```

Getting Started
===============
Pre-built binaries of Apache Tika standalone applications are available
from https://tika.apache.org/download.html . Pre-built binaries of all the
Tika jars can be fetched from Maven Central or your favourite Maven mirror.

**Tika 2.X and support for Java 8 reached End of Life (EOL) in April, 2025. 
See [Tika Roadmap 2.x, 3.x and beyond](https://cwiki.apache.org/confluence/display/TIKA/Tika+Roadmap+--+2.x%2C+3.x+and+Beyond).** 

Tika is based on **Java 17** and uses the [Maven 3](https://maven.apache.org) build system.
**N.B.** [Docker](https://www.docker.com/products/personal) is used for tests in tika-integration-tests. If Docker is not installed, those tests are skipped.

To build Tika from source, use the following command in the main directory:

    ./mvnw clean install

The Maven wrapper (`mvnw`) is included in the repository and will automatically download
the correct Maven version if needed. On Windows, use `mvnw.cmd` instead.

The build consists of a number of components, including a standalone runnable jar that you can use to try out Tika features. You can run it like this:

    java -jar tika-app/target/tika-app-*.jar --help


To build a specific project (for example, tika-server-standard):

    ./mvnw clean install -am -pl :tika-server-standard

If the ossindex-maven-plugin is causing the build to fail because a dependency
has now been discovered to have a vulnerability:

    ./mvnw clean install -Dossindex.skip


Faster Builds
=============

**Fast profile** - Use `-Pfast` to skip tests, checkstyle, and spotless:

    ./mvnw clean install -Pfast

**Parallel builds** - Add `-T1C` to build with 1 thread per CPU core:

    ./mvnw clean install -Pfast -T1C

**Maven Daemon (mvnd)** - Keeps a warm JVM running for 2-3x faster rebuilds:

```bash
# Install: https://github.com/apache/maven-mvnd
# macOS: brew install mvndaemon/tap/mvnd

# Use exactly like mvn
mvnd clean install -Pfast
mvnd test -pl :tika-core
```

**Combine both** for maximum speed during development:

    mvnd clean install -Pfast -T1C


Reproducible Builds
===================

Apache Tika supports [reproducible builds](https://reproducible-builds.org/). This means
that building the same source code with the same JDK version should produce
byte-for-byte identical artifacts, regardless of the build machine or time.

Key configuration:
- `project.build.outputTimestamp` is set in `tika-parent/pom.xml`
- All Maven plugins are configured to produce deterministic output

To verify the build plan supports reproducibility:

    ./mvnw artifact:check-buildplan

To verify two builds produce identical artifacts:

    ./mvnw clean install -DskipTests
    mv ~/.m2/repository/org/apache/tika tika-build-1
    ./mvnw clean install -DskipTests
    diff -r tika-build-1 ~/.m2/repository/org/apache/tika


Maven Dependencies
==================

Apache Tika provides *Bill of Material* (BOM) artifact to align Tika module versions and simplify version management. 
To avoid convergence errors in your own project, import this
bom or Tika's parent pom.xml in your dependency management section.

If you use Apache Maven:

```xml
<project>
  <dependencyManagement>
    <dependencies>
      <dependency>
       <groupId>org.apache.tika</groupId>
       <artifactId>tika-bom</artifactId>
       <version>4.x.y</version>
       <type>pom</type>
       <scope>import</scope>
      </dependency>
    </dependencies>
  </dependencyManagement>

  <dependencies>
    <dependency>
      <groupId>org.apache.tika</groupId>
      <artifactId>tika-parsers-standard-package</artifactId>
      <type>pom</type>
      <!-- version not required since BOM included -->
    </dependency>
  </dependencies>
</project>
```

For Gradle:

```kotlin
dependencies {
  implementation(platform("org.apache.tika:tika-bom:4.x.y"))

  // version not required since bom (platform in Gradle terms)
  implementation("org.apache.tika:tika-parsers-standard-package@pom")
}
```

Migrating to 4.x
================
TBD

Contributing
============
See [CONTRIBUTING.md](CONTRIBUTING.md) and https://tika.apache.org/contribute.html

[![contributors](https://contributors-img.web.app/image?repo=apache/tika)](https://github.com/apache/tika/graphs/contributors)

Building from a Specific Tag
============================
Let's assume that you want to build the 3.0.1 tag:
```
0. Download and install hub.github.com
1. git clone https://github.com/apache/tika.git
2. cd tika
3. git checkout 3.0.1
4. ./mvnw clean install
```

If a new vulnerability has been discovered between the date of the
tag and the date you are building the tag, you may need to build with:

```
4. ./mvnw clean install -Dossindex.skip
```

If a local test is not working in your environment, please notify
 the project at dev@tika.apache.org. As an immediate workaround,
 you can turn off individual tests with e.g.:

```
4. ./mvnw clean install -Dossindex.skip -Dtest=\!UnpackerResourceTest#testPDFImages
```

License (see also LICENSE.txt)
==============================

Collective work: Copyright 2011 The Apache Software Foundation.

Licensed to the Apache Software Foundation (ASF) under one or more contributor license agreements.  See the NOTICE file distributed with this work for additional information regarding copyright ownership.  The ASF licenses this file to You under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.  You may obtain a copy of the License at

<https://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the License for the specific language governing permissions and limitations under the License.

Apache Tika includes a number of subcomponents with separate copyright notices and license terms. Your use of these subcomponents is subject to the terms and conditions of the licenses listed in the LICENSE.txt file.

Export Control
==============

This distribution includes cryptographic software.  The country in which you currently reside may have restrictions on the import, possession, use, and/or re-export to another country, of encryption software.  BEFORE using any encryption software, please  check your country's laws, regulations and policies concerning the import, possession, or use, and re-export of encryption software, to  see if this is permitted.  See <http://www.wassenaar.org/> for more information.

The U.S. Government Department of Commerce, Bureau of Industry and Security (BIS), has classified this software as Export Commodity Control Number (ECCN) 5D002.C.1, which includes information security software using or performing cryptographic functions with asymmetric algorithms.  The form and manner of this Apache Software Foundation distribution makes it eligible for export under the License Exception ENC Technology Software Unrestricted (TSU) exception (see the BIS Export Administration Regulations, Section 740.13) for both object code and source code.

The following provides more details on the included cryptographic software:

Apache Tika uses the Bouncy Castle generic encryption libraries for extracting text content and metadata from encrypted PDF files.  See <http://www.bouncycastle.org/> for more details on Bouncy Castle.  

Mailing Lists
=============

* user@tika.apache.org - About using Tika
* dev@tika.apache.org - About developing Tika

Subscribe by sending a message to `{list}-subscribe@tika.apache.org`.

Issue Tracker
=============

https://issues.apache.org/jira/browse/TIKA

Security
========

See [SECURITY.md](SECURITY.md) and https://tika.apache.org/security.html
