# Validação — Baseline e Verificação Pós-Refatoração

A refatoração só está pronta quando a aplicação **sobe sem erros** e **todos os endpoints da baseline respondem como antes** (mesmo status e mesmo formato de resposta), exceto mudanças de contrato justificadas por segurança.

## 1. Preparar o ambiente (sem poluir o projeto)

| Stack | Comando |
|---|---|
| Python | `python -m venv /tmp/refactor-arch-venv && /tmp/refactor-arch-venv/bin/pip install -r requirements.txt` |
| Node | `npm install` (o `node_modules/` já é ignorado pelo git) |

Use uma porta livre e rode o servidor em background, guardando o log:
```bash
python app.py > /tmp/app.log 2>&1 &      # ou: npm start > /tmp/app.log 2>&1 &
sleep 3 && tail -n 20 /tmp/app.log        # confirmar "Running on ..." / "listening"
```
Se o README exige passos prévios (ex.: `python seed.py`), execute-os antes, nas duas rodadas.

## 2. Baseline (Fase 1, antes de qualquer mudança)

Monte um script de smoke test (salvo **fora** do projeto, ex.: `/tmp/refactor-arch-smoke.sh`) com **uma requisição por endpoint** do inventário, cobrindo:
- caminho feliz de cada rota (GET de lista e de item, POST, PUT, DELETE);
- ao menos um caso de erro por recurso (404 de id inexistente, 400 de payload inválido);
- os exemplos de `*.http`/README, se existirem;
- ordem que respeite dependências (criar antes de atualizar/deletar).

Helper genérico:
```bash
B=${BASE_URL:-http://localhost:5000}
r(){ m=$1; p=$2; d=$3
  if [ -n "$d" ]; then code=$(curl -s -o /tmp/body -w '%{http_code}' -X "$m" -H 'Content-Type: application/json' -d "$d" "$B$p")
  else code=$(curl -s -o /tmp/body -w '%{http_code}' -X "$m" "$B$p"); fi
  echo "$m $p -> $code $(head -c 200 /tmp/body | tr -d '\n')"; }
r GET /health
r POST /recurso '{"campo":"valor"}'
```
Salve a saída como `/tmp/refactor-arch-baseline.txt`. Pare o servidor (`kill %1` ou `fuser -k <porta>/tcp`) e apague artefatos gerados (banco SQLite, `__pycache__`) que não existiam antes.

## 3. Verificação pós-refatoração (Fase 3)

1. **Boot:** suba com o **mesmo comando** de antes. O log não pode ter traceback/stack trace. Com Python, rode também `python -W default app.py` e confirme que os avisos de deprecation tratados sumiram.
2. **Imports/sintaxe:** `python -m compileall -q src app.py` ou `node --check` em cada arquivo.
3. **Endpoints:** rode o mesmo script em banco limpo, salve em `/tmp/refactor-arch-after.txt` e compare:
   ```bash
   diff <(cut -d' ' -f1-4 /tmp/refactor-arch-baseline.txt) <(cut -d' ' -f1-4 /tmp/refactor-arch-after.txt)
   ```
   A comparação de `METHOD rota -> status` deve ser idêntica. Depois confira o corpo das respostas: mesmas chaves no envelope (`dados`, `sucesso`, `erro`, `message`...). Diferenças só são aceitas se estiverem em "Contract changes" com justificativa de segurança.
4. **Varredura de regressão:** repita as buscas do catálogo para cada finding corrigido (ex.: `grep -rnE "execute\(.*\+" src/` não deve retornar nada; `grep -rn "print(" src/` vazio; `grep -rn "utcnow()" src/` vazio).
5. **Casos de segurança:** prove que a correção funciona (ex.: login com `' OR '1'='1` agora retorna 401; endpoint admin sem token retorna 403; resposta de usuário não contém `senha`/`password`).
6. **Limpeza:** pare o servidor, apague bancos gerados, `__pycache__/` e logs dentro do projeto.

## 4. Critérios de saída

| Item | Obrigatório |
|---|---|
| Aplicação inicia sem erros com o comando original | ✓ |
| 100% das requisições da baseline com o mesmo status | ✓ |
| Corpo das respostas com o mesmo envelope/chaves (salvo "Contract changes") | ✓ |
| Nenhuma ocorrência restante dos anti-patterns marcados como corrigidos | ✓ |
| Nenhum arquivo antigo órfão / código morto deixado para trás | ✓ |

Se qualquer item falhar: corrija, rode novamente a verificação inteira e só então imprima o bloco "PHASE 3: REFACTORING COMPLETE".
