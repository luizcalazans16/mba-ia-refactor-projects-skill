================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js 22) + Express ^4.18.2 (sqlite3 ^5.1.6, banco em memória)
Files:   3 analyzed | ~180 lines of code
Date:    2026-11-03

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 3 | LOW: 5

## Findings

### F01 [CRITICAL] Credenciais hardcoded
Catalog: AP-01
File: src/utils.js:2-5
      src/AppManager.js:45
Description: `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`, `dbUser` e `smtpUser` literais no objeto `config`, versionados no git; a chave de produção do gateway é usada em AppManager.js:45.
Impact: Quem tem acesso ao repositório tem a senha do banco e a chave live do gateway de pagamento; rotação exige deploy.
Recommendation: `src/config/index.js` lendo `process.env` (sem defaults reais) + `.env.example` (PB-01).

### F02 [CRITICAL] God Class `AppManager`
Catalog: AP-03
File: src/AppManager.js:4-139
Description: Uma classe cria a conexão (l.7), define schema e seed (l.10-23), registra todas as rotas (l.25-138) e implementa dentro delas o checkout, o "gateway" de pagamento, a criação de usuário, o relatório financeiro e a deleção.
Impact: Nenhuma regra pode ser testada sem subir Express + SQLite; qualquer mudança em um fluxo arrisca os outros; o nome não diz o que a classe faz.
Recommendation: Quebrar em `database/`, `models/` (User, Course, Enrollment, Payment, AuditLog), `controllers/`, `routes/`, `services/` e `createApp.js` (PB-03).

### F03 [CRITICAL] Armazenamento inseguro de senha
Catalog: AP-04
File: src/utils.js:17-23
      src/AppManager.js:68
      src/AppManager.js:18
Description: `badCrypto` repete os 2 primeiros caracteres do base64 da senha e trunca em 10 caracteres — não é hash: é reversível em parte e colide para qualquer senha com o mesmo prefixo. Sem `pwd`, o usuário é criado com a senha padrão `"123456"`; o seed grava `'123'` em texto puro.
Impact: Senhas triviais de recuperar; contas criadas sem senha compartilham uma senha conhecida.
Recommendation: `crypto.scryptSync` com salt aleatório (`node:crypto`, sem dependência nova); nada de senha padrão (PB-04).

### F04 [CRITICAL] Dados de cartão e chave do gateway escritos em log
Catalog: AP-05
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` grava o número completo do cartão e a chave live a cada checkout.
Impact: Violação direta de PCI-DSS; qualquer pessoa com acesso aos logs obtém cartões e a chave do gateway.
Recommendation: Logar apenas os 4 últimos dígitos e nunca a chave (PB-05).

### F05 [CRITICAL] Relatório financeiro administrativo sem proteção
Catalog: AP-06
File: src/AppManager.js:80-129
Description: `GET /api/admin/financial-report` devolve faturamento por curso e o nome e o valor pago por cada aluno, sem qualquer autenticação.
Impact: Dados financeiros e pessoais acessíveis a qualquer cliente da API.
Recommendation: Exigir token de administrador vindo do ambiente (`X-Admin-Token`), desabilitado por padrão (PB-06).

### F06 [HIGH] Escritas multi-etapa sem transação e deleção que deixa órfãos
Catalog: AP-10
File: src/AppManager.js:50-62
      src/AppManager.js:131-137
Description: O checkout insere matrícula, pagamento e log de auditoria em callbacks encadeados sem transação; se o pagamento falhar, a matrícula fica sem pagamento. `DELETE /api/users/:id` apaga só o usuário — a própria resposta admite: "as matrículas e pagamentos ficaram sujos no banco".
Impact: Matrículas sem pagamento (curso liberado sem cobrança) e pagamentos apontando para usuários inexistentes ("Unknown" no relatório).
Recommendation: `BEGIN/COMMIT/ROLLBACK` em um helper `transaction()`; deleção em cascata dentro de transação (PB-09).

### F07 [HIGH] Entrada sem validação derruba o processo
Catalog: AP-14 (elevado a HIGH: um único request derruba a API)
File: src/AppManager.js:35
      src/AppManager.js:46
Description: Só é verificada a presença de `usr`, `eml`, `c_id`, `card`; sem checagem de tipo. Confirmado em execução: `"card": 4111` (número) lança `TypeError: cc.startsWith is not a function` dentro do callback do sqlite, uma exceção não capturada que encerra o processo Node.
Impact: Negação de serviço trivial: qualquer cliente derruba o servidor com um request.
Recommendation: Validar tipos/formatos no controller (strings não vazias, e-mail, `c_id` inteiro, cartão só com dígitos) e rodar o fluxo com `async/await` + middleware de erro (PB-11, PB-12).

### F08 [HIGH] Estado global mutável exportado
Catalog: AP-08
File: src/utils.js:9-15
      src/utils.js:25
Description: `globalCache` e `totalRevenue` são variáveis de módulo exportadas e mutadas por `logAndCache`; o cache cresce sem limite a cada checkout.
Impact: Estado compartilhado escondido entre requisições, impossível de isolar em testes; vazamento de memória.
Recommendation: Classe `InMemoryCache` instanciada no composition root e injetada (PB-08).

### F09 [HIGH] Regras de negócio no handler e acoplamento sem injeção de dependência
Catalog: AP-07, AP-09
File: src/AppManager.js:28-78
      src/AppManager.js:7
      src/app.js:8-10
Description: O handler de checkout decide a aprovação do pagamento (`cc.startsWith("4")`, l.46), cria usuários, matricula, registra auditoria e cacheia. A conexão é criada no construtor (l.7) e a app depende da classe concreta.
Impact: Impossível trocar o gateway fake por um real ou o banco por um dublê sem reescrever a classe.
Recommendation: `CheckoutController` recebendo models, `PaymentGateway`, `PasswordHasher` e cache por construtor; rota fina (PB-07, PB-08).

### F10 [MEDIUM] Query N+1 no relatório financeiro
Catalog: AP-13
File: src/AppManager.js:83-127
Description: 1 query de cursos + 1 query de matrículas por curso + 2 queries (usuário e pagamento) por matrícula, coordenadas por contadores manuais.
Impact: O número de queries cresce linearmente com as matrículas; a lógica de contadores é frágil (resposta pode nunca ser enviada se um callback falhar).
Recommendation: Uma única query com `LEFT JOIN` entre courses, enrollments, users e payments, agrupada em JS (PB-10).

### F11 [MEDIUM] Erros ignorados e tratamento inconsistente
Catalog: AP-16
File: src/AppManager.js:57
      src/AppManager.js:92-93
      src/AppManager.js:104-106
      src/AppManager.js:133-135
Description: Callbacks recebem `err` e não o checam (auditoria, matrículas, usuário, pagamento, deleção); em l.93 `enrollments.length` explode se a query falhar. Cada rota inventa sua própria resposta de erro; não há middleware de erro.
Impact: Falhas silenciosas, respostas que nunca chegam e crashes do processo.
Recommendation: Driver promisificado + `asyncHandler` + middleware `(err, req, res, next)` central que preserva as mensagens de texto atuais (PB-12).

### F12 [MEDIUM] Efeitos colaterais acoplados ao fluxo de pagamento
Catalog: AP-18
File: src/AppManager.js:57-59
      src/utils.js:12-15
Description: Auditoria e cache (`logAndCache`) são executados inline no meio do callback de pagamento, via funções utilitárias globais.
Impact: Não há ponto de extensão para auditoria/cache reais; falha do cache afeta o checkout.
Recommendation: Serviços injetados (`AuditLogModel`, `InMemoryCache`) chamados pelo controller (PB-07, PB-08).

### F13 [LOW] Nomenclatura ruim
Catalog: AP-20
File: src/AppManager.js:29-33
      src/AppManager.js:26
      src/utils.js:17
Description: `u`, `e`, `p`, `cid`, `cc`; `self = this` para contornar `function`; `badCrypto`; `AppManager` (nome sem significado).
Impact: Leitura difícil; o contrato `usr/eml/pwd/c_id/card` vaza para o código interno.
Recommendation: Desestruturar o body para nomes descritivos mantendo o contrato externo (PB-14).

### F14 [LOW] `console.log` como logging
Catalog: AP-21
File: src/AppManager.js:45
      src/utils.js:13
      src/app.js:13
Description: Logs sem nível ou estrutura (um deles com dado sensível, ver F04).
Impact: Logs não filtráveis em produção.
Recommendation: Logger mínimo com níveis, injetado (PB-14).

### F15 [LOW] Código morto
Catalog: AP-22
File: src/utils.js:10
      src/AppManager.js:2
      src/utils.js:2-3
      src/utils.js:5
Description: `totalRevenue` é importado e nunca usado; `dbUser`, `dbPass` e `smtpUser` não são lidos em lugar nenhum.
Impact: Ruído e segredos sem propósito no código.
Recommendation: Remover (PB-14).

### F16 [LOW] Magic numbers e strings
Catalog: AP-19
File: src/AppManager.js:46
      src/AppManager.js:68
      src/utils.js:18
      src/utils.js:6
Description: Regra de aprovação `"4"`, senha padrão `"123456"`, loop de `10000`, porta `3000`, status `'PAID'`/`'DENIED'` literais.
Impact: Regras de negócio escondidas em literais.
Recommendation: Constantes nomeadas na config/serviço de pagamento (PB-14).

### F17 [LOW] Callback hell
Catalog: AP-23
File: src/AppManager.js:37-77
      src/AppManager.js:83-128
Description: Até 6 níveis de callbacks aninhados no checkout e no relatório.
Impact: Fluxo difícil de seguir; erros fáceis de perder (ver F11).
Recommendation: Promisificar o driver e usar `async/await` (PB-15).

## Deprecated APIs
None detected (checked: `express` 4 — nenhum uso de `req.param()`, `res.send(status, body)` ou `body-parser`; `Buffer.from` já é a API moderna; execução com `node --trace-deprecation src/app.js` exercitando todos os endpoints não emitiu avisos).

## Architecture Notes
God class `AppManager` concentra conexão, schema, seed, rotas e todas as regras, com callbacks aninhados e estado global em `utils.js`. A refatoração proposta mantém `npm start` → `src/app.js`, cria `createApp.js` como composition root, `database/` com driver promisificado e transações, models por tabela, controllers (checkout, relatório, usuários), routes (View), services (pagamento, hash de senha, cache, logger) e middleware de erro central. O contrato (`usr/eml/pwd/c_id/card`, mensagens de texto) é preservado.

================================
Total: 17 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
