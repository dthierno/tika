/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.apache.tika;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;

/**
 * IFT3913 - Tâche 3 : test volontairement en échec, désactivé par défaut.
 * <p>
 * Il ne s'exécute qu'avec {@code -Dtika.rickroll.demo=true} (case à cocher
 * « rickroll_demo » du workflow « IFT3913 - Tâche 3 » lancé à la main), afin de
 * démontrer que le CI rickrolle l'équipe dès qu'un cas de test échoue, sans
 * casser la suite de tests réelle de Tika.
 */
@EnabledIfSystemProperty(named = "tika.rickroll.demo", matches = "true")
public class RickrollDemoTest {

    @Test
    public void neverGonnaGiveYouUp() {
        String promesseDeRick = "never gonna give you up";
        String promesseDuTest = "gonna give you up";
        assertEquals(promesseDeRick, promesseDuTest,
                "Ce test vous a laissé tomber. Rick, lui, ne l'aurait jamais fait.");
    }
}
