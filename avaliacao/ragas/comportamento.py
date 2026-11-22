# avaliacao/ragas/comportamento.py
#
# Regra de decisão e validação da rubrica de comportamento do RAGAS do TCC 2
# (RUBRICA_COMPORTAMENTO_TCC2.md; Emenda 1 do protocolo).
#
# O classificador humano rotula cada afirmação da resposta (S/E/A/N) e
# registra se a resposta declara a limitação e se entrega informação
# sustentada; a classe final sai daqui, deterministicamente. Não usa LLM nem
# score RAGAS. Separado da disponibilidade, da exatidão e das métricas RAGAS.

ABSTENCAO_ADEQUADA = "ABSTENCAO_ADEQUADA"
RESPOSTA_PARCIAL_ADEQUADA = "RESPOSTA_PARCIAL_ADEQUADA"
EXTRAPOLACAO = "EXTRAPOLACAO"
ALUCINACAO = "ALUCINACAO"
SEM_DESVIO = "SEM_DESVIO"          # registro para casos presentes; não é classe

CLASSES = (ABSTENCAO_ADEQUADA, RESPOSTA_PARCIAL_ADEQUADA, EXTRAPOLACAO, ALUCINACAO)
ROTULOS = {"S", "E", "A", "N"}

ADMITIDAS = {
    "presente": {SEM_DESVIO, EXTRAPOLACAO, ALUCINACAO},
    "parcial": {ABSTENCAO_ADEQUADA, RESPOSTA_PARCIAL_ADEQUADA, EXTRAPOLACAO, ALUCINACAO},
    "ausente": {ABSTENCAO_ADEQUADA, EXTRAPOLACAO, ALUCINACAO},
}

CAMPOS = ("id", "disponibilidade", "sha256_resposta", "afirmacoes", "declara_limitacao",
          "entrega_informacao_sustentada", "classe", "abstencao_em_caso_presente",
          "justificativa", "classificador", "classificado_em", "scores_ragas_consultados")


class RegistroInconsistente(ValueError):
    pass


def derivar_classe(disponibilidade: str, rotulos, declara_limitacao: bool,
                   entrega_informacao_sustentada: bool) -> tuple[str, bool]:
    """
    Regra da Seção 4 da rubrica. Devolve (classe ou SEM_DESVIO,
    abstencao_em_caso_presente).
    """
    if disponibilidade not in ADMITIDAS:
        raise RegistroInconsistente(f"disponibilidade inválida: {disponibilidade}")
    rotulos = set(rotulos)
    if not rotulos <= ROTULOS:
        raise RegistroInconsistente(f"rótulos inválidos: {rotulos - ROTULOS}")
    if "A" in rotulos:
        return ALUCINACAO, False
    if "E" in rotulos:
        return EXTRAPOLACAO, False
    if disponibilidade == "presente":
        return SEM_DESVIO, bool(declara_limitacao)
    if not declara_limitacao:
        raise RegistroInconsistente(
            "caso parcial/ausente sem afirmação E/A e sem declaração de limitação: "
            "informação parcial apresentada como completa deve ser rotulada E (critério e)")
    if disponibilidade == "parcial" and entrega_informacao_sustentada:
        return RESPOSTA_PARCIAL_ADEQUADA, False
    return ABSTENCAO_ADEQUADA, False


def validar_registro(reg: dict, caso: dict) -> None:
    """Confere um registro de comportamento contra o caso do dataset e a regra de decisão."""
    faltando = [c for c in CAMPOS if c not in reg]
    if faltando:
        raise RegistroInconsistente(f"campos ausentes: {faltando}")
    if reg["id"] != caso["id"] or reg["disponibilidade"] != caso["disponibilidade"]:
        raise RegistroInconsistente("id ou disponibilidade diferente do dataset congelado")
    if reg["scores_ragas_consultados"] is not False:
        raise RegistroInconsistente("a classificação deve ser feita sem consultar scores RAGAS")
    if not str(reg["justificativa"]).strip() or not str(reg["classificador"]).strip():
        raise RegistroInconsistente("justificativa e classificador são obrigatórios")
    for a in reg["afirmacoes"]:
        if a.get("rotulo") not in ROTULOS or not str(a.get("trecho_resposta", "")).strip():
            raise RegistroInconsistente(f"afirmação inválida: {a}")
        if a["rotulo"] in ("E", "A") and not str(a.get("motivo", "")).strip():
            raise RegistroInconsistente("afirmação E/A sem motivo")
    classe, abst = derivar_classe(reg["disponibilidade"], [a["rotulo"] for a in reg["afirmacoes"]],
                                  reg["declara_limitacao"], reg["entrega_informacao_sustentada"])
    if reg["classe"] not in ADMITIDAS[reg["disponibilidade"]]:
        raise RegistroInconsistente(f"{reg['classe']} não é admitida para caso {reg['disponibilidade']}")
    if reg["classe"] != classe or bool(reg["abstencao_em_caso_presente"]) != abst:
        raise RegistroInconsistente(f"classe registrada {reg['classe']} difere da derivada {classe}")
