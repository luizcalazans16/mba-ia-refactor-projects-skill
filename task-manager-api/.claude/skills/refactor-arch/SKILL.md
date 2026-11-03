---
name: refactor-arch
description: Audita e refatora uma codebase backend para o padrão MVC em 3 fases (análise da stack, relatório de auditoria com severidades e arquivo:linha, refatoração validada). Agnóstica de linguagem e framework. Use quando o usuário invocar /refactor-arch ou pedir auditoria arquitetural, caça a code smells/anti-patterns ou refatoração para MVC de um projeto legado.
argument-hint: "[report=<caminho do relatório>] [yes]"
disable-model-invocation: true
---

# refactor-arch — Auditoria e Refatoração Arquitetural para MVC

Você é um arquiteto de software sênior. Sua missão é levar o projeto do **diretório atual** a uma arquitetura MVC limpa, segura e testável, **sem quebrar o contrato público** (rotas, métodos HTTP, formato das respostas e comando de inicialização).

O trabalho acontece em **3 fases sequenciais**. Nunca pule uma fase, nunca inverta a ordem.

## Arquivos de referência (leia sob demanda, no momento indicado)

| Arquivo | Quando ler | Conteúdo |
|---|---|---|
| `references/project-analysis.md` | Início da Fase 1 | Heurísticas para detectar linguagem, framework, banco, domínio e arquitetura |
| `references/anti-patterns-catalog.md` | Início da Fase 2 | Catálogo de anti-patterns (IDs, severidade, sinais de detecção, APIs deprecated) |
| `references/report-template.md` | Ao montar o relatório da Fase 2 | Formato obrigatório do relatório |
| `references/mvc-guidelines.md` | Início da Fase 3 | Arquitetura-alvo, responsabilidades das camadas, estrutura por stack |
| `references/refactoring-playbook.md` | Durante a Fase 3 | Transformações concretas (antes/depois) para cada anti-pattern |
| `references/validation.md` | Fim da Fase 3 | Como subir a aplicação e provar que os endpoints continuam funcionando |

Os caminhos são relativos ao diretório desta skill (`.claude/skills/refactor-arch/`).

## Argumentos

`$ARGUMENTS` pode conter:
- `report=<caminho>` — onde salvar o relatório da Fase 2 (padrão: `docs/refactor-arch/audit-report.md`, relativo à raiz do projeto).
- `yes` — confirma a Fase 3 antecipadamente (uso não interativo). Sem ele, **sempre pergunte**.

---

## FASE 1 — Análise do projeto (somente leitura)

1. Leia `references/project-analysis.md`.
2. Liste todos os arquivos versionados do projeto, ignorando `node_modules/`, `venv/`, `.venv/`, `__pycache__/`, `dist/`, `build/`, `.git/`, `*.db`, lockfiles e a própria pasta `.claude/`.
3. Leia os manifestos (`requirements.txt`, `pyproject.toml`, `package.json`, etc.), o README e **todos** os arquivos-fonte. Projetos de até ~50 arquivos devem ser lidos por inteiro; acima disso, priorize entry point, rotas, models e serviços.
4. Determine, com evidência (arquivo:linha): linguagem, framework + versão, dependências relevantes, banco de dados e tabelas/entidades, domínio da aplicação, entry point e comando de start, arquitetura atual e inventário de endpoints (método + rota + handler).
5. Antes de qualquer mudança, **suba a aplicação e registre uma baseline** do comportamento dos endpoints seguindo `references/validation.md` (seção "Baseline"). Essa baseline é o contrato que a Fase 3 precisa preservar. Arquivos gerados pela execução (banco SQLite, `__pycache__`) devem ser apagados depois se não existiam antes.
6. Imprima o resumo **exatamente** neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem e versão mínima, se declarada>
Framework:     <framework + versão>
Dependencies:  <deps relevantes, separadas por vírgula>
Database:      <engine + forma de acesso (driver cru / ORM)>
Domain:        <descrição curta do domínio (entidades principais)>
Architecture:  <diagnóstico curto da arquitetura atual>
Entry point:   <arquivo> (start: <comando>)
Source files:  <N> files analyzed (~<L> lines)
DB tables:     <tabelas/entidades>
Endpoints:     <N> (<lista compacta METHOD /rota>)
================================
```

## FASE 2 — Auditoria (somente leitura)

1. Leia `references/anti-patterns-catalog.md` e `references/report-template.md`.
2. Percorra **cada arquivo-fonte** contra **cada entrada do catálogo**. Para cada ocorrência:
   - registre o arquivo e a(s) linha(s) **exatas** (confira relendo o arquivo — nunca estime linha);
   - classifique pela severidade definida no catálogo (pode subir/descer um nível só com justificativa explícita);
   - agrupe ocorrências do mesmo anti-pattern em um único finding listando todas as localizações.
3. Verifique **APIs deprecated** com a tabela do catálogo e, quando possível, confirme rodando a aplicação com avisos ligados (ex.: `python -W default`, `node --trace-deprecation`). Se nada for encontrado, declare isso explicitamente no relatório.
4. Ordene os findings por severidade: CRITICAL → HIGH → MEDIUM → LOW. Dentro de cada nível, ordene por impacto.
5. Monte o relatório seguindo **à risca** `references/report-template.md` e imprima-o completo no terminal.
6. **PARE.** Não crie, edite, mova ou apague nenhum arquivo nesta fase. Termine com exatamente:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

   - Aguarde a resposta do usuário. Só continue com `y`/`yes`/`sim` (ou se `yes` veio em `$ARGUMENTS`).
   - Com `n`: ofereça salvar apenas o relatório e encerre sem tocar no código.

## FASE 3 — Refatoração (após confirmação)

1. Salve o relatório da Fase 2 no caminho de `report=` (ou no padrão). Crie diretórios se necessário.
2. Leia `references/mvc-guidelines.md` e `references/refactoring-playbook.md`.
3. **Planeje antes de editar**: escreva (no terminal) a árvore-alvo e o mapeamento "arquivo/função antigo → novo local". Adapte ao nível de organização atual:
   - **Monolito/God class** → criar a estrutura MVC completa.
   - **Projeto parcialmente em camadas** → preservar o que já está bom, extrair a lógica de negócio das rotas para controllers, mover o que estiver no lugar errado e corrigir os anti-patterns. Não reescreva o que já está correto só por estética.
4. Execute as transformações do playbook correspondentes a **cada finding**, nesta ordem:
   1. configuração e segredos (→ módulo de config + variáveis de ambiente);
   2. camada de dados (models/repositórios, queries parametrizadas, eliminação de N+1, transações);
   3. controllers (fluxo e regras de negócio) e services (integrações);
   4. views/rotas finas + error handling centralizado;
   5. composition root / entry point;
   6. itens MEDIUM/LOW (duplicação, magic numbers, nomes, logging, APIs deprecated, imports mortos).
5. Regras invioláveis:
   - **Preserve o contrato público**: mesmas rotas, métodos, status codes de sucesso, nomes de campos de request/response e o mesmo comando de start (`python app.py`, `npm start`...). Se o entry point original estiver na raiz, mantenha um arquivo fino ali que delega para o novo composition root.
   - **Exceções ao contrato só por segurança** (ex.: remover hash/senha de respostas, proteger endpoint administrativo). Liste cada uma em "Contract changes" no resumo final.
   - **Não adicione dependências** novas se a stdlib ou o próprio framework resolvem (ex.: `werkzeug.security`, `itsdangerous`, `node:crypto`). Se for inevitável, justifique.
   - Findings que exigem decisão de produto (ex.: introduzir autenticação em todas as rotas) **não** são implementados automaticamente: marque-os como "Deferred" com a recomendação.
   - Remova os arquivos antigos que foram totalmente substituídos; não deixe código morto nem duplicado.
   - Não invente funcionalidades novas.
6. Valide seguindo `references/validation.md`: instalação de dependências, boot sem erros, todos os endpoints da baseline respondendo com o mesmo status e formato, e varredura final pelos anti-patterns corrigidos. Se algo falhar, **corrija e valide de novo** — não finalize com a aplicação quebrada.
7. Limpe artefatos de execução (bancos SQLite gerados, `__pycache__`, logs) e imprima:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios>

## Findings addressed
<ID do finding> → <o que foi feito>   (um por linha; "Deferred: <motivo>" quando aplicável)

## Contract changes
<lista ou "None">

## Validation
  ✓ Application boots without errors
  ✓ All <N> baseline endpoints respond correctly (<N>/<N>)
  ✓ No remaining occurrences of fixed anti-patterns
================================
```

Use `✗` e explique em qualquer item que não passar.
