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
`ZeroSizeFileDetector` et les tests originaux `ZeroSizeFileDetectorTest`. Elle fixe
le groupe d'opérateurs `DEFAULTS` et produit les rapports HTML et XML. L'adaptateur
`pitest-junit5-plugin` 1.2.3 est une dépendance du plugin PIT. Malgré son nom,
l'exécution fonctionne avec notre JUnit 6.1.3 : PIT ajoute automatiquement le
launcher 6.1.3, découvre les deux tests Jupiter et termine avec succès. La version
JUnit existante est conservée.

PIT est lancé explicitement et n'est pas ajouté au cycle Maven habituel. Pour
comparer les prochaines mesures à M0, il faudra conserver les versions, les
opérateurs et la classe cible ; la sélection des tests sera élargie lorsque de
nouveaux tests seront disponibles.

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

Les commandes suivantes s'exécutent depuis la racine du dépôt, avec le JDK 21
utilisé pour M0. Préparer d'abord le parent et le processeur d'annotations dans
le dépôt Maven local, afin de ne pas dépendre d'une compilation antérieure :

```sh
./mvnw -B -ntp -pl tika-annotation-processor -am install -Dspotless.goal=check
```

Exécuter ensuite les seuls tests originaux et produire une couverture JaCoCo
fraîche :

```sh
./mvnw -B -ntp -pl tika-core -am clean test \
  -Dtest=ZeroSizeFileDetectorTest \
  -Dsurefire.failIfNoSpecifiedTests=false \
  -Djacoco.append=false -Dspotless.goal=check
```

`surefire.failIfNoSpecifiedTests=false` permet aux modules préparatoires, qui ne
contiennent pas le test ciblé, de terminer. Dans `tika-core`, les deux tests ciblés
doivent être exécutés. Le rapport JaCoCo se trouve dans
`tika-core/target/site/jacoco/index.html`.

Exécuter PIT uniquement dans `tika-core`, après la compilation précédente :

```sh
./mvnw -B -ntp -pl tika-core org.pitest:pitest-maven:mutationCoverage
```

Les nouveaux rapports sont écrits dans `tika-core/target/pit-reports/`. Ils peuvent
être remplacés par les exécutions suivantes, sans modifier les preuves archivées
de M0. Les commandes de compilation utilisent `spotless.goal=check` pour vérifier
le formatage sans réécrire les sources.

Pour vérifier toute la suite de tests unitaires de `tika-core` et celle du
processeur d'annotations, sans filtre sur les tests :

```sh
./mvnw -B -ntp -pl tika-core -am clean test \
  -Djacoco.append=false -Dspotless.goal=check
```

Cette dernière commande produit une couverture de la suite entière, distincte de
la couverture ciblée utilisée pour M0. Relancer les commandes ciblées pour comparer
les mesures initiales.

La vérification du setup après `clean` réussit : `tika-core` compte 749 cas de test,
dont 747 exécutés et deux ignorés par les annotations existantes ; le processeur
d'annotations exécute ses huit tests. Il n'y a aucun échec ni erreur. Les deux cas
ignorés sont `reproduceRandomizedTestFailure` (activation réservée à la reproduction
d'un échec) et `testUndeclaredEntityXML` (à retravailler sans Xerces). Aucun test
n'a été désactivé pour ce setup.

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

Le POM racine exclut uniquement `tache2/resultats/M0/**` du contrôle de licence
Apache RAT, car ces preuves sont des fichiers générés conservés sans modification.
Le contrôle reste actif sur le reste du projet.

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

La mesure M0 a été validée avant la préparation du setup. Aucun test IA ou manuel
supplémentaire n'a encore été ajouté. ChatUniTest sera préparé par Andy après la
fusion du setup. Cette section documente uniquement le travail réalisé à ce stade,
conformément aux
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
