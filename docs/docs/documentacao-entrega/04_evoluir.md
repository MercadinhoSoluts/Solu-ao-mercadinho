# 4. Evoluir — Como atualizo sem quebrar? {#evoluir}

Quem lê: arquitetura e líder técnico · Referência: ISO/IEC/IEEE 14764

## 4.1 Inventário de dependências (SBOM) {#e-sbom}

O sistema depende de seis bibliotecas Python, do CLI do Supabase e do cliente JavaScript do Supabase na Edge Function. Duas bibliotecas estão sem versão fixa, o que pode quebrar uma instalação futura sem aviso. O próprio BipSystem é distribuído sob licença MIT.

| Componente | Versão declarada | Onde | Licença | Observação |
| --- | --- | --- | --- | --- |
| Python | 3.14 | Ambiente | PSF | 3.15 incompatível com o Reflex atual |
| reflex | `==0.8.28.post1` | `requirements.txt` | Apache-2.0 | Fixada |
| httpx | `==0.28.1` | `requirements.txt` | BSD-3-Clause | Fixada |
| supabase (Python) | `==2.33.0` | `requirements.txt` | MIT | Fixada |
| plotly | `>=5.24,<7` | `requirements.txt` | MIT | Faixa de versões |
| python-dotenv | sem versão | `requirements.txt` | BSD-3-Clause | Fixar versão |
| sqlalchemy[asyncio] | sem versão | `requirements.txt` | MIT | Fixar versão |
| supabase (CLI) | `^2.121.0` | `package.json` | MIT | Ferramenta de desenvolvimento |
| @supabase/supabase-js | `@2` | Edge Function | MIT | Versão maior fixada |
| PostgreSQL | 17 | Supabase | PostgreSQL | Gerenciado pelo Supabase |

Licenças conforme os projetos de origem; confirmar a cada atualização. Para gerar o inventário completo, com dependências indiretas, rode `pip freeze` no ambiente do projeto e anexe o resultado a cada versão.

## 4.2 Roadmap e dívida técnica {#e-roadmap}

A prioridade é proteger os dados e colocar o sistema no ar de forma estável; só depois virão funcionalidades novas.

| Ordem | Item | Por quê | Pendência |
| --- | --- | --- | --- |
| 1 | Ativar backup (plano Pro ou exportação diária) | Hoje uma perda do banco é irrecuperável | P01 |
| 2 | Ativar proteção contra senhas vazadas e confirmar a regra de papéis do gerente | Segurança de acesso | P02, P03 |
| 3 | Hospedar a aplicação | Sistema independente de um computador local | P04 |
| 4 | Trocar a série fictícia dos relatórios por dados reais | Relatório confiável para decisão | P05 |
| 5 | Concluir as mudanças abertas no OpenSpec: `migrate-to-supabase-backend` (20 de 26 tarefas) e `cashier-sales-flow` (12 de 15) | Fechar o escopo da versão 1 | — |
| 6 | Importar os dados do Xano, se o cliente quiser o histórico antigo | Histórico completo no sistema | P06 |
| 7 | Tela de correção de estoque e destaque de lote vencido | A função existe no banco, falta a tela | P08 |
| 8 | Pipeline que roda os testes a cada pull request | Evitar que código quebrado chegue à `main` | — |

### Dívida técnica

- `bipsystem.py` concentra cerca de 6.900 linhas de telas e estado; dividir em páginas, estados e componentes facilita manutenção e trabalho em paralelo.
- Uma nova entrada com a mesma validade soma ao lote existente e ignora o número de lote informado (ADR 010).
- A mudança `create-employee-registration-api` (1 de 30 tarefas) e os arquivos em `xano/` descrevem a arquitetura antiga e devem ser arquivados.
- Documentos antigos em `docs/` citam Grafana; os gráficos atuais usam Plotly.
- Duas dependências sem versão fixa (4.1).

## 4.3 Changelog e versionamento {#e-changelog}

O sistema adota versionamento semântico (SemVer) a partir desta entrega: MAIOR para mudanças que quebram compatibilidade, MENOR para funcionalidades novas e CORREÇÃO para ajustes. O repositório ainda não tem tags; a primeira deve ser `v1.0.0`, criada no commit `c53f4fe`.

| Versão | Data | Mudanças | Quebra compatibilidade? |
| --- | --- | --- | --- |
| 1.0.0 | 13/11/2026 | Primeira versão entregue ao cliente | — |
| pré-1.0 | 12/11/2026 | Melhoria visual e responsividade da tela inicial | Não |
| pré-1.0 | 02/11/2026 | Relatórios de vendas liberados para gerente e proprietário | Não |
| pré-1.0 | 23/10/2026 | Caixa: compras, itens, pagamento, baixa de estoque por FEFO | Sim: novas tabelas de venda |
| pré-1.0 | 22/10/2026 | Compatibilidade de nomes de papéis | Não |
| pré-1.0 | 17/10/2026 | Esquema inicial no Supabase, substituindo o Xano | Sim: troca de backend |

Cada versão nova acrescenta uma linha no topo desta tabela, e mudanças que quebram compatibilidade vêm com um guia de migração (4.4).

## 4.4 Guias de migração {#e-migracao}

### Dados do Xano para o Supabase (opcional)

Os arquivos em `xano/` descrevem tabelas e endpoints, mas não contêm registros. A versão 1.0 começou do zero no Supabase; este roteiro só é necessário se o cliente quiser o histórico antigo. Nenhum dado deve ser digitado à mão a partir deles. O procedimento completo está em `docs/supabase-cutover-and-xano-data-migration.md`; em resumo:

1. Exportar do Xano, com acesso autenticado, usuários, produtos, códigos de barras, estoque e preços.
2. Validar a exportação com `scripts/validate_xano_export.py`.
3. Mapear cada campo para as tabelas atuais (`products`, `stock_lots`, `product_price_history`, `profiles`), com preços convertidos para centavos.
4. Importar num projeto de teste, conferir contagens e uma amostra de registros.
5. Repetir no projeto de produção e registrar a reconciliação.

### Atualizar uma versão do sistema

1. Ler o changelog (4.3) e o guia da versão, se houver quebra de compatibilidade.
2. Fazer backup do banco (3.5).
3. `git pull` na `main` e `pip install -r requirements.txt`.
4. `supabase db push` para aplicar migrações novas e republicar a Edge Function, se mudou.
5. Rodar os testes de regressão (4.6) e o roteiro de verificação manual.
6. Reiniciar a aplicação.

### Atualizar o Reflex ou o Python

Fazer numa branch separada, alterar a versão em `requirements.txt`, apagar a pasta `.web` (gerada pelo Reflex), reinstalar e rodar todos os testes. Só integrar à `main` com a suíte verde.

## 4.5 Matriz de compatibilidade {#e-compatibilidade}

| Item | Suportado e testado | Observação |
| --- | --- | --- |
| Sistema operacional (desenvolvimento) | Windows | Linux e macOS são suportados pelo Reflex, mas não foram testados pela equipe |
| Python | 3.14 | 3.15 não funciona com Reflex 0.8.28.post1 |
| Reflex | 0.8.28.post1 | Versão fixada |
| Banco | PostgreSQL 17 (Supabase) | Migrações escritas para o Postgres do Supabase |
| Edge Function | Runtime Deno do Supabase | Usa `@supabase/supabase-js` 2 |
| Navegador | Navegadores baseados em Chromium (testado no Brave) | Firefox e Safari não testados |
| Leitor de código de barras | Leitores USB que funcionam como teclado | O campo do caixa aceita digitação ou leitura |
| Resolução | Telas de computador (testado em 1920 × 1080) | Uso em celular não validado |

## 4.6 Testes de regressão {#e-testes}

A suíte automática tem 16 arquivos de teste Python e os testes Deno da Edge Function. Ela não roda sozinha a cada mudança: deve ser executada antes de toda atualização (comandos na aba Manter, seção 2.6).

Depois dos testes automáticos, um roteiro manual de 10 minutos confirma que o essencial não quebrou:

- [ ] Login com operador leva ao caixa; com gerente, ao painel
- [ ] Cadastro de produto de teste e vínculo de preço
- [ ] Entrada de dois lotes com validades diferentes
- [ ] Venda que consome o lote de validade mais próxima
- [ ] Venda recusada por estoque insuficiente, sem baixar nada
- [ ] Venda cancelada, sem baixar nada
- [ ] Relatórios mostram a venda concluída
- [ ] Cadastro e exclusão de funcionário de teste
