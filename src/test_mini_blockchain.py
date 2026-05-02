"""
test_mini_blockchain.py
=======================
Testes didáticos para o mini_blockchain.py.

Cada teste tem um nome descritivo e comentários explicando
o que está sendo verificado e por que aquilo importa.

Como rodar:
    python -m pytest test_mini_blockchain.py -v

O flag -v (verbose) mostra o nome de cada teste — recomendado
para aprendizado, pois os nomes explicam o comportamento.
"""

import pytest
from mini_blockchain import Block, Blockchain


# ===========================================================================
# Testes da classe Block
# ===========================================================================


class TestComputeHash:
    """Testa o cálculo do hash de um bloco."""

    def test_hash_tem_64_caracteres(self):
        """
        SHA-256 sempre produz exatamente 64 caracteres hexadecimais.
        Isso é uma propriedade da função, não do nosso código.
        """
        block = Block(1, [{"tx": "venda PETR4"}], "hash_anterior_qualquer")
        assert len(block.hash) == 64

    def test_hash_e_deterministico(self):
        """
        O mesmo bloco sempre deve produzir o mesmo hash.
        Isso é fundamental: todos os nós da rede precisam chegar
        ao mesmo resultado ao verificar um bloco.
        """
        block = Block(1, [{"tx": "venda PETR4"}], "hash_anterior")
        hash1 = block.compute_hash()
        hash2 = block.compute_hash()
        assert hash1 == hash2

    def test_mudanca_no_conteudo_muda_o_hash(self):
        """
        Esta é a propriedade de segurança central da blockchain.
        Se qualquer campo do bloco mudar (quantidade, remetente, etc.),
        o hash muda completamente — a adulteração fica detectável.
        """
        block = Block(1, [{"quantidade": 1000}], "hash_anterior")
        hash_original = block.compute_hash()

        # Simula adulteração: alguém tenta mudar a quantidade
        block.transactions[0]["quantidade"] = 9999
        hash_adulterado = block.compute_hash()

        assert hash_original != hash_adulterado

    def test_hash_so_contem_caracteres_hexadecimais(self):
        """
        SHA-256 usa representação hexadecimal: apenas 0-9 e a-f.
        """
        block = Block(0, [], "0")
        assert all(c in "0123456789abcdef" for c in block.hash)


class TestMine:
    """
    Testa o Proof of Work (PoW).

    O mine() é o mecanismo que torna a blockchain resistente a fraudes:
    para adicionar um bloco, é preciso realizar trabalho computacional.
    Reescrever o histórico exigiria refazer esse trabalho para todos os
    blocos subsequentes — inviável na prática.
    """

    def test_hash_comeca_com_zeros_apos_mineracao(self):
        """
        Após mine(difficulty=3), o hash DEVE começar com "000".
        Esse é o critério de aceitação do Proof of Work.
        """
        block = Block(1, [{"tx": "compra VALE3"}], "hash_anterior")
        block.mine(difficulty=3)
        assert block.hash.startswith("000")

    def test_difficulty_maior_exige_mais_zeros(self):
        """
        difficulty=4 exige "0000" no início do hash.
        Cada zero adicional torna a mineração ~16x mais difícil
        (porque há 16 caracteres hex possíveis).
        """
        block = Block(1, [{"tx": "teste"}], "hash_anterior")
        block.mine(difficulty=4)
        assert block.hash.startswith("0000")

    def test_nonce_e_incrementado_durante_mineracao(self):
        """
        O nonce começa em 0 e é incrementado a cada tentativa frustrada.
        Após a mineração, o nonce deve ser > 0 (na enorme maioria dos casos),
        provando que o computador trabalhou para encontrar o hash válido.
        """
        block = Block(1, [{"tx": "liquidação DVP"}], "hash_anterior")
        assert block.nonce == 0
        block.mine(difficulty=3)
        # É estatisticamente impossível encontrar o hash válido na primeira tentativa
        assert block.nonce > 0

    def test_hash_permanece_valido_apos_mineracao(self):
        """
        Após mine(), o hash armazenado no bloco deve bater com
        o hash calculado a partir do seu conteúdo.
        Isso garante consistência interna.
        """
        block = Block(1, [{"tx": "emissão de debênture"}], "hash_anterior")
        block.mine(difficulty=3)
        assert block.hash == block.compute_hash()


# ===========================================================================
# Testes da classe Blockchain
# ===========================================================================


class TestBlockchainInit:
    """Testa a inicialização da blockchain."""

    def test_blockchain_começa_com_bloco_genesis(self):
        """
        Toda blockchain começa com o bloco Genesis (índice 0).
        Ele é o ponto de partida compartilhado por todos os nós da rede.
        """
        bc = Blockchain()
        assert len(bc.chain) == 1
        assert bc.chain[0].index == 0

    def test_genesis_tem_previous_hash_zero(self):
        """
        O bloco Genesis não tem predecessor, então seu previous_hash é "0".
        Isso é uma convenção universal em blockchains.
        """
        bc = Blockchain()
        assert bc.chain[0].previous_hash == "0"

    def test_blockchain_nova_e_valida(self):
        """
        Uma blockchain recém-criada (só com Genesis) deve ser válida.
        """
        bc = Blockchain()
        assert bc.is_valid() is True


class TestAddTransaction:
    """
    Testa a adição de transações (blocos) à blockchain.

    No mercado de capitais, cada transação pode representar:
    - Liquidação de compra/venda de ação (DVP)
    - Transferência de custódia
    - Emissão de título
    """

    def test_adicionar_transacao_aumenta_cadeia(self):
        """
        Cada transação cria um novo bloco. Após 3 transações,
        a cadeia deve ter 4 blocos (Genesis + 3).
        """
        bc = Blockchain()
        bc.add_transaction("FundoA", "FundoB", "PETR4", 1000, 38.50)
        bc.add_transaction("FundoB", "FundoC", "VALE3", 500, 67.20)
        bc.add_transaction("FundoC", "FundoA", "LFT_2027", 100, 1000.0)
        assert len(bc.chain) == 4  # Genesis + 3 transações

    def test_transacao_registra_dados_corretamente(self):
        """
        Os dados da transação devem ser preservados fielmente no bloco.
        Num ledger real, isso garante o registro auditável da operação.
        """
        bc = Blockchain()
        block = bc.add_transaction(
            sender="Custodiante_BTG",
            receiver="Custodiante_Itau",
            asset="NTNB_2035",
            quantity=50,
            price=1200.0,
        )
        tx = block.transactions[0]
        assert tx["sender"] == "Custodiante_BTG"
        assert tx["receiver"] == "Custodiante_Itau"
        assert tx["asset"] == "NTNB_2035"
        assert tx["quantity"] == 50
        assert tx["price"] == 1200.0
        assert tx["total"] == 60000.0  # 50 * 1200

    def test_blocos_estao_encadeados_corretamente(self):
        """
        O previous_hash de cada bloco deve ser igual ao hash do bloco anterior.
        Esse encadeamento é o que torna a adulteração detectável:
        mudar um bloco quebra todos os elos subsequentes.
        """
        bc = Blockchain()
        bc.add_transaction("A", "B", "PETR4", 100, 38.0)
        bc.add_transaction("B", "C", "PETR4", 100, 39.0)

        bloco_1 = bc.chain[1]
        bloco_2 = bc.chain[2]

        assert bloco_2.previous_hash == bloco_1.hash

    def test_blocos_adicionados_passam_no_proof_of_work(self):
        """
        Todo bloco adicionado via add_transaction passa pelo mine().
        O hash deve começar com "000" (difficulty=3 padrão).
        """
        bc = Blockchain()
        block = bc.add_transaction("A", "B", "VALE3", 200, 67.0)
        assert block.hash.startswith("000")

    def test_indices_sao_sequenciais(self):
        """
        Os índices dos blocos devem ser 0, 1, 2, 3...
        Facilita auditoria e busca por bloco específico.
        """
        bc = Blockchain()
        bc.add_transaction("A", "B", "PETR4", 100, 38.0)
        bc.add_transaction("B", "C", "VALE3", 50, 67.0)

        for i, block in enumerate(bc.chain):
            assert block.index == i


class TestIsValid:
    """
    Testa a detecção de adulteração.

    Esse é o coração da proposta de valor da blockchain:
    qualquer modificação no histórico é detectável imediatamente.
    """

    def test_cadeia_integra_e_valida(self):
        """
        Uma blockchain usada normalmente deve ser sempre válida.
        """
        bc = Blockchain()
        bc.add_transaction("FundoA", "FundoB", "PETR4", 1000, 38.50)
        bc.add_transaction("FundoB", "FundoC", "VALE3", 500, 67.20)
        assert bc.is_valid() is True

    def test_adulteracao_de_quantidade_invalida_cadeia(self):
        """
        CENÁRIO DE ATAQUE: alguém tenta alterar a quantidade de uma transação
        passada para se beneficiar (ex: inflar uma posição).

        Como o hash do bloco adulterado muda, o bloco seguinte (que armazena
        o hash antigo em previous_hash) detecta a inconsistência.
        """
        bc = Blockchain()
        bc.add_transaction("FundoA", "FundoB", "PETR4", 1000, 38.50)
        bc.add_transaction("FundoB", "FundoC", "PETR4", 200, 39.0)

        # Ataque: alterar a quantidade do primeiro bloco após o Genesis
        bc.chain[1].transactions[0]["quantity"] = 999999

        assert bc.is_valid() is False

    def test_adulteracao_de_remetente_invalida_cadeia(self):
        """
        CENÁRIO DE ATAQUE: alguém tenta alterar o remetente de uma transação
        para falsificar a origem de um ativo.
        """
        bc = Blockchain()
        bc.add_transaction("FundoLegitimo", "FundoB", "NTNB_2035", 100, 1200.0)

        # Ataque: trocar o remetente
        bc.chain[1].transactions[0]["sender"] = "FundoFraudulento"

        assert bc.is_valid() is False

    def test_remocao_de_bloco_invalida_cadeia(self):
        """
        CENÁRIO DE ATAQUE: alguém tenta apagar uma transação do histórico.
        Por exemplo, remover o registro de uma liquidação já realizada.

        Com blockchain, isso também é detectável: os índices e hashes
        ficam inconsistentes.
        """
        bc = Blockchain()
        bc.add_transaction("A", "B", "PETR4", 100, 38.0)
        bc.add_transaction("B", "C", "PETR4", 100, 39.0)
        bc.add_transaction("C", "D", "PETR4", 100, 40.0)

        # Ataque: remover o bloco do meio
        del bc.chain[2]

        assert bc.is_valid() is False


# ===========================================================================
# Testes de integração — simulação realista de mercado de capitais
# ===========================================================================


class TestCenarioMercadoDeCapitais:
    """
    Simula fluxos reais de mercado de capitais usando a blockchain.
    Estes testes integram todas as funcionalidades anteriores.
    """

    def test_liquidacao_sequencial_de_ativos(self):
        """
        CENÁRIO: Liquidação em cadeia — ativo passa por 3 fundos.
        Reflete o fluxo: negociação → liquidação → custódia.

        Fundo A vende PETR4 → Fundo B
        Fundo B vende PETR4 → Fundo C
        Verifica que todo o histórico está registrado e íntegro.
        """
        bc = Blockchain()
        bc.add_transaction("Fundo_A", "Fundo_B", "PETR4", 1000, 38.50)
        bc.add_transaction("Fundo_B", "Fundo_C", "PETR4", 1000, 39.00)

        assert len(bc.chain) == 3
        assert bc.is_valid() is True

        # Auditoria: verificar o rastro completo do ativo
        liquidacao_1 = bc.chain[1].transactions[0]
        liquidacao_2 = bc.chain[2].transactions[0]

        assert liquidacao_1["sender"] == "Fundo_A"
        assert liquidacao_1["receiver"] == "Fundo_B"
        assert liquidacao_2["sender"] == "Fundo_B"
        assert liquidacao_2["receiver"] == "Fundo_C"

    def test_multiplos_ativos_no_ledger(self):
        """
        CENÁRIO: Um ledger pode registrar transações de diferentes ativos.
        Reflete um custodiante que opera ações, títulos e cotas simultaneamente.
        """
        bc = Blockchain()
        bc.add_transaction("FundoRF", "FundoMulti", "LFT_2027", 100, 1050.0)
        bc.add_transaction("FundoRV", "FundoMulti", "VALE3", 500, 67.20)
        bc.add_transaction("FundoMulti", "FundoHedge", "PETR4", 300, 38.50)

        assert len(bc.chain) == 4
        assert bc.is_valid() is True

        ativos = [bc.chain[i].transactions[0]["asset"] for i in range(1, 4)]
        assert "LFT_2027" in ativos
        assert "VALE3" in ativos
        assert "PETR4" in ativos

    def test_registro_de_total_financeiro(self):
        """
        O campo 'total' (quantity * price) deve ser calculado corretamente.
        Numa liquidação DVP real, o total em R$ é o que o comprador paga.
        """
        bc = Blockchain()
        block = bc.add_transaction(
            sender="FundoVendedor",
            receiver="FundoComprador",
            asset="PETR4",
            quantity=2000,
            price=38.50,
        )
        assert block.transactions[0]["total"] == pytest.approx(77_000.0)
