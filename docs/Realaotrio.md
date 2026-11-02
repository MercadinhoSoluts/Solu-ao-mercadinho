# Relatório de trabalho — migração do BIPSYSTEM para Supabase

**Estado atual:** a migração está em andamento; **8 de 26 tarefas** da change `migrate-to-supabase-backend` estão marcadas como concluídas. A validação OpenSpec estrita passou.

## 1. Decisões e planejamento

Foram registrados no OpenSpec o escopo e as decisões aprovadas:

- Supabase será a base de autenticação e persistência, com Reflex acessando o serviço pelo servidor.
- O projeto começa vazio: **não serão importados usuários, produtos, estoque ou preços do Xano**. O Xano permanece preservado para consulta histórica, sem sincronização ou fallback automático.
- Operadores podem cadastrar produtos e receber estoque; correções de estoque ficam restritas a gerentes e proprietários.
- Gerentes podem administrar somente contas de operadores; proprietários podem atribuir qualquer cargo.
- Alterações de preço devem preservar o histórico, embora a tela exiba o preço atual.
- PDV e Relatórios continuam fora da migração de persistência porque são telas de placeholder.

Os documentos da change incluem proposta, design, tarefas e especificações de autenticação, funcionários, produtos, estoque, preços e fundação Supabase, em `openspec/changes/migrate-to-supabase-backend`.

## 2. Banco e segurança no Supabase

O projeto `jsmmzjnulxmxlprrqgcn` foi vinculado pelo CLI. Como Docker/WSL local não estava disponível, a validação foi feita no projeto remoto, conforme aprovado.

Foi criada e aplicada a migration versionada `20261017180000_initial_application_schema.sql`. Ela cria:

- `profiles`, sincronizada com `auth.users`;
- `products`;
- `stock_lots`;
- `inventory_movements`, como histórico de movimentações;
- `product_price_history`, com histórico imutável de preços;
- a view `current_product_prices`;
- políticas RLS, funções transacionais para recebimento/correção de estoque, triggers, restrições e índices.

**Verificação do banco após a aplicação:** 5 tabelas públicas, 5 com RLS, 7 políticas, uma versão registrada no histórico de migrations e nenhum usuário, perfil ou registro de teste persistido. O banco começou sem tabelas públicas e sem usuários Auth.

Os testes SQL foram executados em transações revertidas. Verificaram sincronização de perfis, soma de recebimentos sem perder o rótulo original do lote, gravação de movimentações, bloqueio de correção para operador e autorização de correção para gerente. Chamadas anônimas REST a produtos e à RPC de recebimento foram recusadas.

## 3. Configuração do cliente e Edge Function

Foi acrescentado o `.env.example`, com nomes de variáveis e sem valores de credenciais.

A dependência Python `supabase==2.33.0` foi adicionada a `requirements.txt`. O cliente server-side em `supabase_client.py` lê configuração explícita, usa cliente por requisição, não persiste sessão e permite passar o JWT do usuário para operações sob RLS.

Também foi criada a Edge Function de funcionários em `index.ts`, com verificação do JWT, leitura do perfil e cargo armazenados no banco e operações Auth Admin. As regras reutilizáveis estão em `employee_policy.ts`, e `verify_jwt` foi ativado na configuração da função em `config.toml`.

**Importante:** a Edge Function foi verificada e testada localmente, mas ainda **não foi implantada nem exercitada em CRUD ponta a ponta**.

## 4. Testes e limitações de validação

- Cliente Supabase: **5 testes passaram** em `test_supabase_client.py`.
- Edge Function: `deno check` passou; **11 testes passaram** em `employee_policy_test.ts`.
- OpenSpec: a validação estrita passou.
- A suíte Python completa passou: **84 testes aprovados** em Python 3.14. O Python 3.15 ainda não é compatível com a versão Reflex usada (`0.8.28.post1`), por isso a versão recomendada está documentada no README.
- A consulta de histórico do CLI por conexão direta também depende da senha do Postgres. A migration, porém, foi registrada no banco por meio da Management API. **Nenhuma senha ou chave privilegiada foi solicitada ou incluída neste relatório.**

Como contexto anterior à migração, a interface de Preços com mocks já havia sido implementada, e uma validação anterior havia registrado compilação Reflex e 32 testes/11 subtestes aprovados. Esses resultados são anteriores à integração Supabase.

## 5. O que falta para concluir

Ainda restam **18 tarefas** em `tasks.md`:

1. **Autenticação e funcionários (2.4–2.6):** substituir login, sessão e logout por Supabase Auth; conectar o CRUD da tela de funcionários; implementar e documentar bootstrap seguro do primeiro proprietário.
2. **Produtos e estoque (3.1–3.4):** conectar cadastro, consulta, recebimento e inventário; validar concorrência, permissões e atomicidade.
3. **Preços (4.1–4.3):** substituir os mocks por consulta e persistência Supabase, mantendo histórico imutável e pesquisa.
4. **Comportamento operacional (5.1–5.4):** documentar o início sem importação, os estados de carregamento/erro e remover chamadas Xano apenas depois que cada fluxo Supabase estiver verificado.
5. **Integração e cutover (6.1–6.4):** executar testes completos, revisar segurança e documentar implantação, bootstrap e condições de corte.

**Prioridade para quem assumir:** preparar a configuração segura da Edge Function e implementar primeiro a troca de autenticação e o bootstrap do proprietário. O projeto tem zero usuários Auth, então ainda não há uma conta proprietária nem um JWT real para testar a sequência autenticada completa. O Xano continua sendo o backend de runtime do aplicativo até as tarefas de migração e validação serem concluídas.