#!/usr/bin/env python3
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""IFT3913 - Tâche 3 : rickroll quand un cas de test échoue.

Lit les rapports JUnit XML (Surefire), puis :
  * affiche une bannière dans le journal du job,
  * crée une annotation ::error par test en échec, avec le lien vers la vidéo,
  * ajoute un résumé Markdown (miniature cliquable + liste des tests) au job,
  * expose le nombre de tests en échec dans la sortie ``failed-tests``.

Bibliothèque standard uniquement : rien à installer sur le runner.
"""

import glob
import os
# Exception Semgrep justifiee (python.lang.security.use-defused-xml) : les rapports
# analyses sont produits par notre propre execution de Surefire dans le meme job,
# ils ne viennent pas d'un tiers. De plus, expat (Python >= 3.7.1) ne resout pas les
# entites externes. defusedxml imposerait une dependance a installer sur le runner.
import xml.etree.ElementTree as ET  # nosemgrep: python.lang.security.use-defused-xml.use-defused-xml

VIDEO_URL = os.environ.get("VIDEO_URL", "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
THUMBNAIL = "https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg"

# Couplets originaux (parodie) : un par test en échec, en boucle
VERSES = [
    "Ce test t'a laissé tomber... mais Rick, lui, ne te laissera jamais tomber.",
    "Ton oracle a dit non. Rick, lui, ne dira jamais adieu.",
    "Le build est rouge, mais l'amour de Rick reste vert.",
    "Tu connais les règles (du test unitaire), et moi aussi.",
    "Un assert a menti et t'a fait du mal. Rick ne ferait jamais ça.",
]

BANNER = r"""
  _   _
 | \ | | _____   _____ _ __    __ _  ___  _ __  _ __   __ _
 |  \| |/ _ \ \ / / _ \ '__|  / _` |/ _ \| '_ \| '_ \ / _` |
 | |\  |  __/\ V /  __/ |    | (_| | (_) | | | | | | | (_| |
 |_| \_|\___| \_/ \___|_|     \__, |\___/|_| |_|_| |_|\__,_|
                              |___/   ...fail you up?
"""


def failed_tests(pattern):
    """Retourne [(classe, méthode, message)] pour chaque <testcase> en échec ou en erreur."""
    failures = []
    for path in sorted(glob.glob(pattern, recursive=True)):
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        for case in root.iter("testcase"):
            problem = case.find("failure")
            if problem is None:
                problem = case.find("error")
            if problem is None:
                continue
            message = (problem.get("message") or problem.get("type") or "").strip()
            failures.append((case.get("classname", "?"), case.get("name", "?"),
                             message.splitlines()[0] if message else ""))
    return failures


def escape_annotation(text):
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def main():
    failures = failed_tests(os.environ.get("REPORTS_GLOB", "**/target/surefire-reports/TEST-*.xml"))

    print(BANNER)
    print(f"{len(failures)} cas de test en échec. Vous venez de vous faire rickroller : {VIDEO_URL}")

    for i, (cls, name, message) in enumerate(failures):
        verse = VERSES[i % len(VERSES)]
        detail = f"{cls}.{name} : {message}" if message else f"{cls}.{name}"
        print(f"::error title=Never gonna let you down::"
              f"{escape_annotation(detail)}%0A{escape_annotation(verse)}%0A{VIDEO_URL}")
    if not failures:
        # le build Maven a échoué sans rapport exploitable (ex. erreur de compilation des tests)
        print(f"::error title=Never gonna let you down::La suite de tests a échoué. {VIDEO_URL}")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as out:
            out.write("## 🎵 Never gonna fail you up\n\n")
            out.write(f"[![Cliquez ici pour voir pourquoi le test a échoué]({THUMBNAIL})]({VIDEO_URL})\n\n")
            if failures:
                out.write(f"Cas de test qui vous ont laissé tomber : **{len(failures)}**\n\n")
                out.write("| Classe | Test | Message | Rick dit |\n|---|---|---|---|\n")
                for i, (cls, name, message) in enumerate(failures):
                    msg = (message.replace("&", "&amp;").replace("<", "&lt;")
                           .replace(">", "&gt;").replace("|", "\\|")[:200])
                    out.write(f"| `{cls}` | `{name}` | {msg} | _{VERSES[i % len(VERSES)]}_ |\n")
            else:
                out.write("La suite de tests a échoué avant de produire des rapports.\n")

    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as out:
            out.write(f"failed-tests={len(failures)}\n")


if __name__ == "__main__":
    main()
