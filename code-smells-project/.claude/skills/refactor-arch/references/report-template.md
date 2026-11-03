# Template do Relatório de Auditoria (Fase 2)

O relatório é impresso no terminal ao fim da Fase 2 e salvo (após confirmação) como Markdown. Siga este formato **exatamente** — o mesmo template é usado em qualquer stack, o que permite comparar projetos.

## Regras

1. Cabeçalhos e rótulos em inglês (como abaixo); descrições em português.
2. **Um finding por anti-pattern por causa raiz.** Várias ocorrências do mesmo problema → um finding com várias linhas em `File:`.
3. `File:` sempre com `caminho/relativo:linha` ou `caminho:inicio-fim`. Nunca "vários arquivos", nunca linha aproximada.
4. Ordem: CRITICAL → HIGH → MEDIUM → LOW. Numere os findings sequencialmente (`F01`, `F02`...) — os IDs são usados na Fase 3.
5. `Catalog:` referencia o ID do catálogo (`AP-xx`).
6. `Summary` deve bater com a contagem real dos findings.
7. A seção `Deprecated APIs` é obrigatória (mesmo que vazia: "none detected").
8. Sem achismos: cada finding precisa de evidência verificável na linha citada.

## Template

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório>
Stack:   <Linguagem> + <Framework versão>
Files:   <N> analyzed | ~<L> lines of code
Date:    <AAAA-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### F01 [CRITICAL] <Nome do anti-pattern>
Catalog: AP-xx
File: <arquivo>:<linha(s)>
      <arquivo>:<linha(s)>          (uma localização por linha, se houver várias)
Description: <o que acontece, citando o trecho relevante>
Impact: <consequência concreta: segurança, manutenção, performance, testes>
Recommendation: <transformação a aplicar — referencie o playbook PB-xx>

### F02 [HIGH] ...

## Deprecated APIs
| API | Location | Modern replacement |
|---|---|---|
| <api> | <arquivo:linha> | <substituto> |
(ou: "None detected (checked: <o que foi verificado>)")

## Architecture Notes
<2–5 linhas: diagnóstico geral da arquitetura atual e da direção de refatoração proposta>

================================
Total: <N> findings
================================
```

## Exemplo de finding bem escrito

```markdown
### F02 [CRITICAL] SQL Injection
Catalog: AP-02
File: models.py:28
      models.py:47-50
      models.py:110
Description: IDs e campos do request são concatenados nas queries (`"SELECT * FROM produtos WHERE id = " + str(id)`, `"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`).
Impact: `POST /login` aceita `' OR '1'='1` como senha e autentica sem credenciais; qualquer campo de texto permite ler/alterar o banco.
Recommendation: Usar placeholders `?` com tupla de parâmetros em todas as queries (PB-02).
```

## Exemplo de finding mal escrito (não faça)

```markdown
### [HIGH] Código ruim
File: vários
Description: O código tem problemas de qualidade.
```
