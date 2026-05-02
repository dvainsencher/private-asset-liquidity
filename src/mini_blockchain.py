"""
mini_blockchain.py
==================
Implementação didática de um blockchain para estudo de DLT.

Objetivo: desmistificar o mecanismo interno antes de usar ferramentas prontas.
Cada classe e método tem docstring explicando O QUÊ faz, POR QUÊ existe
e como se conecta ao contexto de mercado de capitais.
"""

import hashlib
import json
from datetime import datetime


class Block:
    """
    Representa um bloco dentro de uma blockchain.

    Um bloco é a unidade básica de armazenamento. Pense nele como
    uma página de um livro-razão que contém:
      - Um conjunto de transações (os registros da página)
      - Um selo de integridade (o hash)
      - Uma referência à página anterior (previous_hash)

    Essa referência encadeada é o que dá o nome "blockchain":
    cada bloco aponta para o anterior, formando uma corrente.
    Se alguém adulterar um bloco do passado, o encadeamento quebra
    e a fraude fica detectável.

    Parâmetros
    ----------
    index : int
        Posição do bloco na cadeia. O bloco 0 é o Genesis.
    transactions : list[dict]
        Lista de transações contidas neste bloco.
        No contexto de mercado de capitais, cada transação pode
        representar uma ordem de compra, liquidação DVP, etc.
    previous_hash : str
        Hash do bloco anterior. É o "elo" da corrente.
        O bloco Genesis usa "0" por convenção (não tem anterior).
    """

    def __init__(self, index: int, transactions: list, previous_hash: str):
        self.index = index
        self.timestamp = datetime.utcnow().isoformat()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0  # Será incrementado pelo método mine()
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        """
        Calcula o hash (impressão digital) deste bloco.

        Um hash SHA-256 é uma função que transforma qualquer texto em uma
        string de 64 caracteres hexadecimais. Propriedades importantes:
          - Determinística: o mesmo input sempre produz o mesmo output.
          - Irreversível: não dá para descobrir o input a partir do output.
          - Sensível: qualquer mudança mínima no input muda completamente o output.

        Por que serializar como JSON com sort_keys=True?
        Para garantir que a ordem dos campos não altere o hash.
        {"a":1,"b":2} e {"b":2,"a":1} produziriam hashes diferentes
        sem sort_keys, o que causaria inconsistências entre nós da rede.

        Retorna
        -------
        str
            String hexadecimal de 64 caracteres representando o hash do bloco.

        Exemplo
        -------
        >>> b = Block(1, [{"tx": "venda"}], "abc123")
        >>> len(b.compute_hash())
        64
        >>> b.compute_hash() == b.compute_hash()  # determinístico
        True
        """
        block_data = json.dumps(
            {
                "index": self.index,
                "timestamp": self.timestamp,
                "transactions": self.transactions,
                "previous_hash": self.previous_hash,
                "nonce": self.nonce,
            },
            sort_keys=True,
        )
        return hashlib.sha256(block_data.encode()).hexdigest()

    def mine(self, difficulty: int = 3) -> None:
        """
        Executa Proof of Work (PoW): torna a adição de um bloco computacionalmente cara.

        PROBLEMA que o mine() resolve
        ------------------------------
        Se qualquer nó pudesse adicionar blocos instantaneamente, seria trivial
        reescrever o histórico. Num ledger de mercado de capitais sem PoW,
        um participante desonesto poderia apagar uma transação de liquidação
        e roubar ativos.

        COMO FUNCIONA
        -------------
        Um hash SHA-256 parece aleatório: "a3f91bc2...". O mine() exige que
        o hash comece com `difficulty` zeros, ex: "000a3f91bc2...".

        Como o hash é determinístico, a única forma de obter um hash diferente
        é mudar o input. Por isso existe o `nonce`: um número que incrementamos
        até encontrar um hash válido.

        Exemplo com difficulty=3:
          nonce=0   → hash = "a3f91b..." → NÃO começa com "000" → tenta de novo
          nonce=1   → hash = "77c4d2..." → NÃO começa com "000" → tenta de novo
          ...
          nonce=847 → hash = "000ac2..." → ✅ começa com "000" → aceito!

        CUSTO vs. VERIFICAÇÃO
        ---------------------
        Encontrar o nonce certo pode exigir milhares de tentativas (caro).
        Verificar se o hash é válido leva 1 operação (barato).
        Essa assimetria é o mecanismo de segurança.

        POR QUE MERCADO DE CAPITAIS GERALMENTE NÃO USA PoW
        ---------------------------------------------------
        PoW consome muita energia e é lento (~10min por bloco no Bitcoin).
        Redes permissioned para capital markets usam mecanismos alternativos
        (PBFT, RAFT) que são rápidos e não desperdiçam energia — estudaremos
        isso nas fases seguintes.

        Parâmetros
        ----------
        difficulty : int
            Número de zeros que o hash deve começar. Quanto maior, mais lento.
            difficulty=3 → ~0.001s | difficulty=5 → ~0.1s | difficulty=7 → ~10s
        """
        prefix = "0" * difficulty
        while not self.hash.startswith(prefix):
            self.nonce += 1
            self.hash = self.compute_hash()


class Blockchain:
    """
    Cadeia de blocos: o ledger distribuído simplificado.

    Mantém a lista de blocos e garante a integridade da cadeia.
    Numa rede real, cada participante (nó) teria sua própria cópia
    desta cadeia, e todas deveriam ser idênticas.

    No contexto de mercado de capitais, a Blockchain representa o
    livro-razão compartilhado entre participantes: corretoras, custodiantes,
    câmaras de compensação, etc.
    """

    def __init__(self):
        """
        Inicializa a blockchain criando o bloco Genesis.

        O bloco Genesis é o bloco #0, criado pelo fundador da rede.
        Ele não tem previous_hash real (usa "0" por convenção).
        Todos os participantes precisam concordar com o Genesis para
        participar da mesma rede.
        """
        self.chain = [self._create_genesis()]

    def _create_genesis(self) -> Block:
        """
        Cria o bloco inicial (Genesis) da blockchain.

        O prefixo "_" indica método interno — não deve ser chamado
        diretamente pelo código externo.

        Retorna
        -------
        Block
            O bloco #0 com previous_hash="0" e uma transação simbólica.
        """
        return Block(0, [{"msg": "Genesis Block — início do ledger"}], "0")

    @property
    def last_block(self) -> Block:
        """
        Retorna o bloco mais recente da cadeia.

        Usado internamente para encadear novos blocos:
        o previous_hash do novo bloco deve ser o hash do último bloco.

        Retorna
        -------
        Block
            O último bloco adicionado à cadeia.
        """
        return self.chain[-1]

    def add_transaction(
        self,
        sender: str,
        receiver: str,
        asset: str,
        quantity: float,
        price: float = 0.0,
    ) -> Block:
        """
        Cria um novo bloco com uma transação e o adiciona à cadeia.

        No contexto de capital markets, uma transação representa a
        transferência de um ativo financeiro entre dois participantes.
        Exemplos: liquidação de ações, transferência de cotas de fundo,
        movimentação de títulos públicos.

        O bloco novo sempre aponta para o hash do último bloco existente,
        mantendo o encadeamento.

        Parâmetros
        ----------
        sender : str
            Quem está enviando o ativo (ex: "Fundo_Alfa", "Custodiante_BTG").
        receiver : str
            Quem está recebendo o ativo.
        asset : str
            Identificador do ativo financeiro (ex: "PETR4", "LFT_2027").
        quantity : float
            Quantidade do ativo sendo transferida.
        price : float, opcional
            Preço unitário na transação. Padrão 0 (transferência sem pagamento).

        Retorna
        -------
        Block
            O bloco recém-criado e adicionado à cadeia.

        Exemplo
        -------
        >>> bc = Blockchain()
        >>> block = bc.add_transaction("FundoA", "FundoB", "PETR4", 1000, 38.50)
        >>> block.transactions[0]["asset"]
        'PETR4'
        """
        transaction = {
            "sender": sender,
            "receiver": receiver,
            "asset": asset,
            "quantity": quantity,
            "price": price,
            "total": quantity * price,
        }
        new_block = Block(
            index=len(self.chain),
            transactions=[transaction],
            previous_hash=self.last_block.hash,
        )
        new_block.mine(difficulty=3)
        self.chain.append(new_block)
        return new_block

    def is_valid(self) -> bool:
        """
        Verifica se toda a cadeia está íntegra (não foi adulterada).

        Percorre todos os blocos e faz duas verificações:
          1. O previous_hash do bloco atual bate com o hash do bloco anterior?
             → Garante que o encadeamento não foi quebrado.
          2. O hash atual corresponde ao conteúdo do bloco?
             → Garante que o conteúdo do bloco não foi alterado.

        Numa rede real com múltiplos nós, qualquer nó pode rodar is_valid()
        na cadeia recebida de outro nó para detectar adulteração.

        Retorna
        -------
        bool
            True se a cadeia está íntegra. False se houve adulteração.

        Exemplo
        -------
        >>> bc = Blockchain()
        >>> bc.add_transaction("A", "B", "PETR4", 100, 38.0)
        >>> bc.is_valid()
        True
        >>> bc.chain[1].transactions[0]["quantity"] = 9999  # adulteração!
        >>> bc.is_valid()
        False
        """
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Verificação 1: encadeamento
            if current.previous_hash != previous.hash:
                return False

            # Verificação 2: integridade do conteúdo
            if current.hash != current.compute_hash():
                return False

        return True
