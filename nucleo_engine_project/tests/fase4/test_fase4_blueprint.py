"""F4 — Tests del Album Blueprint MVP (spec DMD Control Center v1.4, §8, §12.1).

Ejecución:  python3 -m pytest tests/album/test_blueprint.py -q
            python3 -m pytest tests/album -q   (desde la raíz del proyecto)

Alcance:
  A. Esquema del blueprint (dmd-album-blueprint/1): validación fail-fast.
  B. Vocabulario armónico: pool de tónica + vecinas ≤1 alteración (RA4).
  C. Derivación por la ruta real F2 (intérprete → capas A/B → compilador).
  D. Determinismo: mismo blueprint ⇒ mismos album.json/docs byte a byte.
  E. Reglas de álbum §8.4 (RA1–RA4) + P-03 (motivo firma, anti-monotonía).
  F. Inyección del motivo por la vía del contrato (development.*).
  G. Variaciones del protagonista (§8.1): mismo / registro_distinto /
     rol_acompanante (solos[] Advanced).
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from album import blueprint as BP  # noqa: E402
from album.esquema import AlbumInvalido  # noqa: E402
from dark_director import compilador as CD  # noqa: E402

GOLDEN = ROOT / "albumes" / "ecos_de_neblina" / "blueprint.json"


def _spec():
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


def _derivar(tmpdir, spec=None):
    spec = spec or _spec()
    return BP.derivar_album(spec, tmpdir)


class TestEsquema(unittest.TestCase):
    """A. Validación fail-fast del schema dmd-album-blueprint/1."""

    def test_golden_carga_con_solo_aviso_informativo(self):
        spec, avisos = BP.cargar_blueprint(GOLDEN)
        self.assertEqual(spec["schema"], "dmd-album-blueprint/1")
        for a in avisos:
            self.assertTrue(a.startswith("W-B1"), a)  # solo el aviso de registro

    def test_schema_desconocido_rechazado(self):
        spec = _spec()
        spec["schema"] = "dmd-album/1"
        with self.assertRaises(BP.ErrorBlueprint) as ctx:
            BP.validar_blueprint(spec)
        self.assertTrue(any("B102" in e for e in ctx.exception.errores))

    def test_campo_desconocido_rechazado(self):
        spec = _spec()
        spec["mood"] = "80%"
        with self.assertRaises(BP.ErrorBlueprint) as ctx:
            BP.validar_blueprint(spec)
        self.assertTrue(any("B109" in e and "mood" in e
                            for e in ctx.exception.errores))

    def test_identidad_archivada_rechazada(self):
        spec = _spec()
        spec["identidad"]["style"] = "doom_triphop"
        with self.assertRaises(BP.ErrorBlueprint) as ctx:
            BP.validar_blueprint(spec)
        self.assertTrue(any("B104" in e for e in ctx.exception.errores))

    def test_original_excluido_de_paleta(self):
        spec = _spec()
        spec["identidad"]["paleta_perfiles"] = ["original", "full"]
        with self.assertRaises(BP.ErrorBlueprint) as ctx:
            BP.validar_blueprint(spec)
        self.assertTrue(any("B113" in e for e in ctx.exception.errores))

    def test_ids_duplicados_rechazados(self):
        spec = _spec()
        spec["arco"][1]["id"] = spec["arco"][0]["id"]
        with self.assertRaises(BP.ErrorBlueprint) as ctx:
            BP.validar_blueprint(spec)
        self.assertTrue(any("B115" in e and "duplicado" in e
                            for e in ctx.exception.errores))

    def test_solo_igual_al_protagonista_rechazado(self):
        spec = _spec()
        spec["arco"][2]["solo"] = "sax_tenor"
        with self.assertRaises(BP.ErrorBlueprint) as ctx:
            BP.validar_blueprint(spec)
        self.assertTrue(any("B119" in e for e in ctx.exception.errores))

    def test_solo_sin_rol_acompanante_rechazado(self):
        spec = _spec()
        spec["arco"][0]["solo"] = "rhodes"
        with self.assertRaises(BP.ErrorBlueprint) as ctx:
            BP.validar_blueprint(spec)
        self.assertTrue(any("B118" in e for e in ctx.exception.errores))

    def test_semillas_fuera_de_rango_rechazadas(self):
        spec = _spec()
        spec["semilla_album"] = 999_900
        with self.assertRaises(BP.ErrorBlueprint) as ctx:
            BP.validar_blueprint(spec)
        self.assertTrue(any("B105" in e and "excede" in e
                            for e in ctx.exception.errores))

    def test_frase_con_campos_desconocidos_rechazada(self):
        spec = _spec()
        spec["motivo_firma"]["frase"][0]["intensidad"] = 0.8
        with self.assertRaises(BP.ErrorBlueprint) as ctx:
            BP.validar_blueprint(spec)
        self.assertTrue(any("B109" in e and "intensidad" in e
                            for e in ctx.exception.errores))

    def test_frase_fuera_de_compases_rechazada(self):
        spec = _spec()
        spec["motivo_firma"]["frase"][0]["bar"] = 9
        with self.assertRaises(BP.ErrorBlueprint) as ctx:
            BP.validar_blueprint(spec)
        self.assertTrue(any("B124" in e for e in ctx.exception.errores))


class TestVocabularioArmonico(unittest.TestCase):
    """B. Pool de tonalidades (vocabulario armónico base, §8.1 + RA4)."""

    def test_pool_f_menor(self):
        pool, errores = BP._pool_tonalidades("F minor")
        self.assertEqual(errores, [])
        self.assertEqual(pool[0], "F minor")
        self.assertEqual(set(pool[1:]), {"Bb minor", "C minor"})
        # el pool es el VOCABULARIO (cada tonalidad ≤1 alteración de la tónica);
        # RA4 pairwise se valida sobre las tonalidades ASIGNADAS por pista.
        for k in pool:
            self.assertLessEqual(abs(BP._armadura_de(k) - BP._armadura_de("F minor")), 1)
        asignadas = BP._keys_por_pista(pool, 3)
        arm = [BP._armadura_de(k) for k in asignadas]
        for i, a in enumerate(arm):
            for b in arm[i + 1:]:
                self.assertLessEqual(abs(a - b), 1)   # RA4 pairwise por construcción

    def test_modo_mayor_rechazado(self):
        pool, errores = BP._pool_tonalidades("F major")
        self.assertIsNone(pool)
        self.assertTrue(any("B202" in e for e in errores))

    def test_asignacion_por_pista_alternada(self):
        pool, _ = BP._pool_tonalidades("F minor")
        keys = BP._keys_por_pista(pool, 3)
        self.assertEqual(keys, ["F minor", "Bb minor", "F minor"])


class TestNivelEnergia(unittest.TestCase):
    """D. Posición del arco [0..1] → control Energía (bandas documentadas)."""

    def test_bandas(self):
        casos = {"muy_baja": (0.0, 0.15, 0.19), "baja": (0.2, 0.35, 0.39),
                 "media": (0.4, 0.5, 0.59), "alta": (0.6, 0.75, 0.79),
                 "muy_alta": (0.8, 0.9, 1.0)}
        for nivel, valores in casos.items():
            for v in valores:
                self.assertEqual(BP.nivel_energia(v), nivel, v)


class TestDerivacion(unittest.TestCase):
    """C + D. Derivación por la ruta real F2 y determinismo byte a byte."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.a, cls.r_a, avisos_a, cls.reglas_a = _derivar(cls._tmp.name + "/a")
        cls.b, cls.r_b, avisos_b, cls.reglas_b = _derivar(cls._tmp.name + "/b")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_album_spec_valido_para_el_pipeline_fase8(self):
        from album import esquema as ES
        avisos = ES.validar_album(self.a)          # fail-fast del esquema real
        self.assertIsInstance(avisos, list)
        self.assertEqual(self.a["schema"], "dmd-album/1")
        self.assertEqual(self.a["album"], "Ecos de Neblina")
        self.assertEqual(self.a["curva_energia"], [0.45, 0.78, 0.15])

    def test_planes_pasaron_capas_ab(self):
        from control_center import validador
        for i, r in enumerate(self.r_a):
            doc_path = ROOT / "albumes" / "ecos_de_neblina" / r["doc"]
            doc = json.loads(doc_path.read_text(encoding="utf-8"))
            self.assertEqual(doc["schema"], "dark-director/1")
            self.assertEqual(doc["harmony"]["key"], r["tonalidad"])

    def test_determinismo_bytes(self):
        raiz = ROOT / "albumes" / "ecos_de_neblina"
        spec = _spec()
        BP.escribir_salida(spec, self.a, self.r_a, [], self.reglas_a,
                           Path(self._tmp.name) / "a")
        BP.escribir_salida(spec, self.b, self.r_b, [], self.reglas_b,
                           Path(self._tmp.name) / "b")
        for sub in ("album.json",):
            b1 = (Path(self._tmp.name) / "a" / sub).read_bytes()
            b2 = (Path(self._tmp.name) / "b" / sub).read_bytes()
            self.assertEqual(b1, b2, sub)
        dorado = (raiz / "album.json").read_bytes()
        self.assertEqual(b1, dorado, "album.json dorado en disco != derivación")
        for r in self.r_a:
            d1 = (Path(self._tmp.name) / "a" / r["doc"]).read_bytes()
            d2 = (Path(self._tmp.name) / "b" / r["doc"]).read_bytes()
            self.assertEqual(d1, d2, r["doc"])
            d3 = (raiz / r["doc"]).read_bytes()
            self.assertEqual(d1, d3, "doc dorado en disco != derivación: " + r["doc"])

    def test_resolucion_determinista(self):
        claves = ("id", "seed", "tonalidad", "perfil_resuelto", "solos",
                  "energia_media_plan", "sha256_doc", "motivo_firma")
        for x, y in zip(self.r_a, self.r_b):
            for k in claves:
                self.assertEqual(x[k], y[k], "%s.%s" % (x["id"], k))

    def test_perfiles_resueltos_en_paleta(self):
        paleta = set(_spec()["identidad"]["paleta_perfiles"])
        for r in self.r_a:
            self.assertIn(r["perfil_resuelto"], paleta, r["id"])


class TestReglas(unittest.TestCase):
    """E. Reglas de álbum §8.4 sobre la derivación dorada."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        _, cls.res, _, cls.reglas = _derivar(cls._tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_todas_las_reglas_pass(self):
        self.assertTrue(self.reglas["todas_ok"],
                        json.dumps(self.reglas["reglas"], ensure_ascii=False))
        ids = {r["id"] for r in self.reglas["reglas"]}
        self.assertEqual(ids, {"RA1", "RA2", "RA3", "RA4", "P03"})

    def test_ra1_contraste(self):
        ra1 = next(r for r in self.reglas["reglas"] if r["id"] == "RA1")
        reales = [r for r in self.res if r["energia_media_plan"] < BP.ENERGIA_CONTRASTE]
        self.assertEqual([r["id"] for r in reales], ["marea_baja_de_neon"])

    def test_ra2_perfiles_distintos(self):
        perfiles = [r["perfil_resuelto"] for r in self.res]
        self.assertEqual(len(set(perfiles)), 3, perfiles)

    def test_ra4_tonicas_relacionadas(self):
        arm = [BP._armadura_de(r["tonalidad"]) for r in self.res]
        self.assertLessEqual(abs(arm[0] - arm[1]), 1)
        self.assertLessEqual(abs(arm[1] - arm[2]), 1)

    def test_p03_motivo_presente_y_ausente(self):
        con = [r["id"] for r in self.res if r["motivo_firma"]]
        sin = [r["id"] for r in self.res if not r["motivo_firma"]]
        self.assertEqual(con, ["umbral_de_neblina", "camara_de_espejos"])
        self.assertEqual(sin, ["marea_baja_de_neon"])


class TestMotivoFirma(unittest.TestCase):
    """F. Inyección del motivo por la vía del contrato (P-03 vía a)."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        _, cls.res, _, _ = _derivar(cls._tmp.name)
        cls.docs = {}
        for r in cls.res:
            cls.docs[r["id"]] = json.loads(
                (Path(cls._tmp.name) / r["doc"]).read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def _dev(self, tid):
        return self.docs[tid].get("development") or {}

    def test_orden_del_doc_coincide_con_produce(self):
        for tid, doc in self.docs.items():
            claves = list(doc)
            self.assertEqual(claves[-1], "ending", tid)
            if self._dev(tid):
                self.assertEqual(claves[-2], "development", tid)
            else:
                self.assertNotIn("development", claves, tid)

    def test_frase_y_recurrencia_en_pista_1(self):
        dev = self._dev("umbral_de_neblina")
        phrases = dev["melody"]["phrases"]
        self.assertIn("verse_2", phrases)
        self.assertEqual([n["pitch"] for n in phrases["verse_2"]],
                         [65, 68, 72, 70, 67])
        self.assertEqual(dev["motifs"]["firma_neblina"]["from_section"], "verse_2")
        self.assertEqual(dev["motifs"]["firma_neblina"]["sections"], ["chorus_4"])
        self.assertEqual(dev["motifs"]["firma_neblina"]["transpose_st"], 0)

    def test_motivo_transpuesto_en_pista_2(self):
        dev = self._dev("camara_de_espejos")
        pitches = [n["pitch"] for n in dev["melody"]["phrases"]["verse_2"]]
        self.assertEqual(pitches, [70, 73, 77, 75, 72])   # +5 st (F→Bb minor)
        self.assertEqual(dev["motifs"]["firma_neblina"]["sections"], ["chorus_8"])

    def test_pista_3_sin_motivo(self):
        self.assertEqual(self._dev("marea_baja_de_neon"), {})

    def test_docs_compilan_en_el_contrato_real(self):
        for tid, doc in self.docs.items():
            CD.compilar(json.loads(json.dumps(doc)))   # fail-fast del contrato
            self.assertEqual(doc["schema"], "dark-director/1")

    def test_notas_del_motivo_en_registro_del_lead(self):
        lo, hi = BP.REGISTRO_LEAD
        for tid in ("umbral_de_neblina", "camara_de_espejos"):
            for n in self._dev(tid)["melody"]["phrases"]["verse_2"]:
                self.assertGreaterEqual(n["pitch"], lo, (tid, n))
                self.assertLessEqual(n["pitch"], hi, (tid, n))


class TestVariacionesProtagonista(unittest.TestCase):
    """G. Variaciones del protagonista (§8.1) vía vocabulario real del intérprete."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        _, cls.res, _, _ = _derivar(cls._tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_mismo(self):
        r = self.res[0]
        self.assertEqual(r["protagonista_intencion"], "sax_tenor")
        self.assertEqual(r["variacion_protagonista"]["regla"], "mismo")
        self.assertEqual(r["solos"], [])

    def test_registro_distinto(self):
        r = self.res[1]
        self.assertEqual(r["protagonista_intencion"], "vibraphone")
        self.assertEqual(r["variacion_protagonista"]["regla"], "registro_distinto")
        self.assertEqual([s["instrument"] for s in r["solos"]], ["vibraphone"])
        self.assertEqual(r["perfil_resuelto"], "full")

    def test_rol_acompanante(self):
        r = self.res[2]
        self.assertEqual(r["protagonista_intencion"], "sax_tenor")
        self.assertEqual(r["variacion_protagonista"]["variacion"], "rol_acompanante")
        self.assertEqual(r["variacion_protagonista"]["regla"],
                         "solos[] Advanced (§9.2)")
        self.assertEqual([s["instrument"] for s in r["solos"]], ["rhodes"])
        self.assertEqual(r["perfil_resuelto"], "sax_rhodes")

    def test_solo_materializado_en_slot_break_bridge(self):
        r = self.res[2]
        sid = r["variacion_protagonista"]["solo_materializado"]["section_id"]
        tipos = {s[0]: s[1] for s in r["secciones"]}
        self.assertIn(tipos[sid], ("break", "bridge"), (sid, tipos))

    def test_rotation_determinista(self):
        self.assertEqual(BP.ROTACION_REGISTRO["sax_tenor"], "vibraphone")
        self.assertEqual(BP.ROTACION_REGISTRO["vibraphone"], "rhodes")
        self.assertEqual(BP.ROTACION_REGISTRO["rhodes"], "sax_tenor")


class TestIntegracionPlanificador(unittest.TestCase):
    """El album.json derivado pasa el planificador real (dry-run)."""

    def test_plan_dry_run_sin_avisos_bloqueantes(self):
        from album import esquema as ES, planificador as PL
        spec, _ = ES.cargar_album(
            ROOT / "albumes" / "ecos_de_neblina" / "album.json")
        plan, avisos = PL.planificar(spec, ROOT / "albumes" / "ecos_de_neblina")
        self.assertEqual(plan["errores_documentos"], [])
        graves = [a for a in avisos if not a.startswith(("W-A1", "W-A8"))]
        self.assertEqual(graves, [], graves)
        curva = plan["analisis"]["curva_energia"]
        self.assertLessEqual(max(curva["desviacion"]), 0.15,
                             "desviación de curva fuera de tolerancia W-A8")


if __name__ == "__main__":
    unittest.main()
