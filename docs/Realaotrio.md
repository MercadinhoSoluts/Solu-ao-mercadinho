# Guia de configuração do Supabase — Sistema do Mercadinho

Este guia define a configuração do Supabase como banco de dados relacional e backend REST/Auth do sistema, substituindo a antiga infraestrutura no Xano. O Supabase não deve ser tratado como um servidor PostgreSQL de acesso direto irrestrito pelo Reflex: a leitura e gravação passam pelo SDK (`supabase-js`), que se comunica com a API PostgREST, onde o **Row Level Security (RLS)** e as **Stored Procedures (RPC)** garantem as regras de negócio e verificações de acesso.

> O workspace do Supabase será o destino planejado da migração; consulte [Estado atual da integração](#estado-atual-da-integração) antes de assumir que todas as tabelas, RLS e funções já foram configuradas.

## Workspace informado

- Painel administrativo: [Dashboard do Supabase](https://supabase.com/dashboard/projects) (requer autenticação na conta Supabase autorizada).
- Este link abre a interface de gerenciamento do workspace; não é uma URL de API e não deve ser usada pelo Reflex como endereço do banco.
- Para conectar a aplicação, obtenha no painel a URL base da API (`SUPABASE_URL`) e a chave pública anônima (`SUPABASE_ANON_KEY`). **Não compartilhar** a senha do banco, token de serviço (`Service Role Key`) ou chave administrativa no repositório ou na conversa.

## Estado atual da integração (Migração Xano ➔ Supabase)

- A infraestrutura anterior (Xano workspace `169507-0`) está sendo descontinuada. O ambiente atual no Supabase deve refletir a mesma arquitetura de dados e segurança.
- O controle de usuários migrou da antiga tabela `user` para o **Supabase Auth** (`auth.users`). E-mails possuem normalização nativa no Supabase. O controle de cargo (`role`) foi migrado para uma nova tabela `public.profiles`, contendo `id`, `name`, `role` (`operator`, `manager`, `owner`) e `is_active` (valor inicial `true`).
- **Testes de Autenticação e CORS:** O processo de *signup* deve definir o usuário sempre como `operator` por padrão, exigindo que um gestor/dono altere o papel posteriormente, ou o *signup* de novos operadores deve ser feito de dentro da plataforma por usuários autorizados (via Edge Function ou Service Role no backend). Testes anteriores com `teste@mercadinho.com` e rejeição de duplicatas (`TESTE@mercadinho.com`) são cobertos nativamente pelo Supabase Auth. Senhas devem ter limite mínimo de 12 caracteres (configurável no painel do Supabase Auth).
- **CORS:** O Supabase reflete automaticamente o CORS para as origens configuradas. Certifique-se de adicionar `http://localhost:3000` (e o domínio de produção) na lista de origens permitidas no painel de API do Supabase, bloqueando origens não confiáveis (`https://example.invalid`).
- Ainda faltam na nova infraestrutura testes concorrentes de duplicidade de estoque (via transação atômica no banco), mapeamento HTTP externo de validação e verificação do `inventory_movements`. O código Reflex precisa ter as chamadas refatoradas do Axios/Fetch puro para o cliente `@supabase/supabase-js`, garantindo o fluxo de sessão autenticada (JWT) ponta a ponta.

## 1. Arquitetura de acesso

```text
Navegador / Reflex
       │ HTTPS + SDK Supabase (Sessão JWT)
       ▼
API PostgREST / RPC do Supabase ─── Políticas RLS, Triggers e Validações
       │
       ▼
Banco relacional PostgreSQL nativo (Supabase)

Grafana ─── Usuário PostgreSQL read-only restrito (banco direto)

O Supabase é a fonte de verdade para produtos, lotes, vendas, caixa e movimentações.

O Reflex chama a API do Supabase pelo backend da aplicação utilizando o SDK. Não enviar tokens de serviço (Service Role) ao navegador.

O Grafana conecta-se diretamente ao PostgreSQL do Supabase utilizando um usuário de leitura dedicado (grafana_reader). Não expor credenciais administrativas nem acesso irrestrito às tabelas para o Grafana.

Usar projetos/workspaces separados (Supabase CLI / Local Dev) para desenvolvimento/testes e produção. Não testar importações ou baixas no ambiente de produção.

 2. Preparação do workspace
Acessar o Dashboard do Supabase com a conta autorizada; criar o projeto "Sistema do Mercadinho".

Configurar os ambientes de desenvolvimento e produção (Local/Remote via Supabase CLI), mantendo schemas e configurações sincronizados via Migrations.

Usar a tabela auth.users existente no Supabase; não criar tabela própria de senhas. Criar a tabela public.profiles e um Trigger para populá-la automaticamente no signup.

Criar as tabelas listadas na seção Modelo de dados via Editor SQL.

Obrigatório: Habilitar Row Level Security (RLS) em todas as tabelas criadas (ALTER TABLE x ENABLE ROW LEVEL SECURITY;).

Aplicar as políticas (Policies) RLS em cada tabela conforme a Matriz de permissões.

Criar a função PL/pgSQL transacional para o fluxo de checkout (process_checkout), que cuidará do FEFO e baixa atômica.

Configurar as variáveis SUPABASE_URL e SUPABASE_ANON_KEY no ambiente do Reflex. Nunca versionar tokens.

Validar o fluxo de venda e FEFO usando os casos da seção Verificação antes de produção.

3. Modelo de dados
Use os IDs gerados pelo Supabase (UUID com default gen_random_uuid()) para as chaves primárias. Configure referências (Foreign Keys) nos campos indicados e índices (B-tree) para buscas. Valores monetários são armazenados como inteiros em centavos; quantidades são numéricas (decimal) para permitir unidades fracionadas.

Tabela	Campos recomendados	Regras e índices
auth.users	Campos nativos do Supabase.	Gerenciado pela plataforma. Senhas criptografadas.
profiles	id (FK auth.users); name (texto); role (enum: operator, manager, owner); is_active (booleano)	Não armazenar senha. Apenas dono/gestor pode alterar o role de outros usuários (via RLS).
categories	id; name (texto); is_active (booleano); created_at (data/hora)	Nome obrigatório; índice para busca por nome.
products	id; barcode (texto, opcional); name (texto); category_id (FK categories, opcional); sale_price_cents (inteiro); unit (enum: unit, kg, g, l, ml, pack); minimum_stock (numérico); is_perishable (booleano); is_active (booleano); created_by (FK profiles); created_at	Preço e limite não negativos. Código de barras único quando informado. Indexar código de barras e nome.
lots	id; product_id (FK products); expiration_date (data, opcional); quantity_received (numérico); quantity_remaining (numérico); received_at (data/hora); created_by (FK profiles)	Quantidades não negativas; validade obrigatória para perecíveis. Indexar product_id, validade e saldo para consulta FEFO.
sales	id; operator_id (FK profiles); status (enum: completed, cancelled); payment_method (enum: cash, card, pix); total_cents (inteiro); request_id (UUID); created_at; cancelled_at (opcional)	request_id único para idempotência. Total não negativo. Venda cancelada não deve apagar o histórico.
sale_items	id; sale_id (FK sales); product_id (FK products); quantity (numérico); unit_price_cents (inteiro); subtotal_cents (inteiro)	Quantidade positiva. Guardar preço praticado na venda. Indexar sale_id.
inventory_movements	id; product_id (FK); lot_id (FK); sale_id e sale_item_id (FK opcionais); type (enum: purchase, bulk_entry, sale, damage, loss, correction, reversal); quantity (positivo); direction (in, out); reason (texto); created_by (FK); created_at	Histórico imutável. RLS bloqueia UPDATE/DELETE. Toda alteração de saldo gera movimentação via sistema.
cash_sessions	id; opened_by e closed_by (FK profiles); status (open, closed); opening_cash_cents (inteiro); expected_cash_cents, counted_cash_cents, difference_cents (inteiros); opened_at, closed_at; notes (texto)	Máximo uma sessão aberta por caixa. Diferença calculada via função no banco, não confiada ao cliente.
alerts	id; type (low_stock, expiring_lot, cash_anomaly); priority (low, medium, high); message (texto); product_id, lot_id (FK); status (open, resolved, dismissed); deduplication_key (texto); due_date (data)	Chave única para ocorrência. Ao surgir nova após resolução, gerar nova chave. Indexar status e tipo.
Estoque e histórico
lots.quantity_remaining é o saldo disponível do lote usado para decidir se a venda pode ser concluída. inventory_movements é o histórico imutável. Não permitir que a interface faça "UPDATE" direto em quantity_remaining. Uma venda, correção ou avaria aciona uma Stored Procedure que altera o saldo do lote e insere a movimentação na mesma operação.

4. Contratos iniciais (Integração Reflex + SDK Supabase)
O Reflex deve utilizar o SDK @supabase/supabase-js. As rotas REST antigas dão lugar a chamadas estruturadas de banco validadas pelo RLS.

Ação / Caminho Lógico	Chamada SDK (Supabase)	Acesso	Uso
POST /auth/login	supabase.auth.signInWithPassword(...)	Público	Autenticar usuário (com limite nativo de tentativas).
GET /auth/me	supabase.auth.getUser() + JOIN profiles	Autenticado	Retornar identidade e papel (role) atrelado.
GET /products	supabase.from('products').select('*')	Autenticado	Listar produtos ativos com paginação e filtros.
GET /products/by-barcode	supabase.from('products').select('*').eq('barcode', 'x')	Autenticado	Localizar item no PDV.
POST/PATCH /products	supabase.from('products').upsert(...)	Conforme RLS	Criar/editar cadastro.
POST /inventory/...	supabase.from('lots').insert(...)	Gestor / Dono	Registrar entrada (Gera trigger p/ movement).
POST /sales/checkout	supabase.rpc('process_checkout', payload)	Autenticado	Validar venda, consumir FEFO atomicamente.
GET /sales	supabase.from('sales').select(...)	Conforme RLS	Consultar vendas (Operador vê as próprias).
POST /sales/{id}/cancel	supabase.rpc('cancel_sale', { id })	Gestor / Dono	Cancelamento auditável com reversão.
POST /cash-sessions/...	supabase.from('cash_sessions').insert/update	Conforme RLS	Abrir/fechar caixa (cálculo em banco).
GET /alerts	supabase.from('alerts').select(...)	Gestor / Dono	Consultar alertas abertos.
Exemplo de solicitação de venda (Checkout)
O cliente envia identificadores e quantidades para a RPC, não os subtotais:

JSON
{
  "p_request_id": "7f2e2a10-81de-4f64-9c56-40c48fb6b770",
  "p_payment_method": "pix",
  "p_items": [
    { "product_id": "uuid-do-produto-1", "quantity": 2 },
    { "product_id": "uuid-do-produto-2", "quantity": 0.5 }
  ]
}
No Reflex: await supabase.rpc('process_checkout', payload).
A Função do PostgreSQL processará a transação. Se o p_request_id for repetido (idempotência), a RPC retorna o ID da venda anterior. Respostas de erro serão lançadas nativamente pelo PostgreSQL e capturadas no frontend.

5. Matriz de permissões (Via RLS)
Aplicar as permissões como Políticas do Banco de Dados (Row Level Security). Ocultar botões no Reflex é interface, não segurança.

Ação	Operador	Gestor	Dono
Consultar produtos e registrar venda	Sim	Sim	Sim
Cadastrar produto, entrada/lote ou avaria	Sim	Sim	Sim
Fazer correção de saldo e cancelar venda	Não	Sim	Sim
Consultar fechamento e finanças	Não	Sim	Sim
Abrir/fechar sessão de caixa	Sim	Sim	Conforme política
Consultar dashboard e alertas	Sim	Sim	Sim
Gerenciar usuários (profiles) e papéis	Não	Conforme política	Sim
Regra: O RLS deve validar que um cliente nunca passe seu próprio role arbitrariamente; o papel deve ser validado via sub-query no PostgreSQL (SELECT role FROM profiles WHERE id = auth.uid()).

6. Regras de negócio obrigatórias no backend (PostgreSQL)
Finalização de venda e FEFO (Stored Procedure Atômica)
Implementar process_checkout como uma Função PL/pgSQL com transação atômica (BEGIN ... COMMIT):

Autenticar usuário (auth.uid()) e validar papel.

Checar request_id em sales. Se existir, retornar venda existente imediatamente.

Para cada item: validar ativo, forma de pagamento e total de saldo.

Consulta FEFO: SELECT * FROM lots WHERE product_id = X AND quantity_remaining > 0 ORDER BY expiration_date ASC NULLS LAST FOR UPDATE; (O FOR UPDATE bloqueia a linha contra concorrência).

Abater as quantidades nos lotes. Se o lote zerar, passar para o próximo.

Gravar em sales e sale_items com preço unitário do momento.

Disparar INSERT automático em inventory_movements.

Se qualquer verificação falhar (ex: falta estoque de 1 item), toda a função realiza ROLLBACK automático e não deduz nada.

Não colocar esse fluxo em produção sem testar concorrência (duas vendas consumindo o último item simultaneamente).

Outras regras
Avarias/Perdas gravam em inventory_movements gerando ajuste.

Cancelamentos acionam função cancel_sale que estorna lotes na ordem inversa e grava reversal no inventário. O registro da venda nunca é apagado (DELETE), apenas atualizado o status.

Fechamento de caixa calcula diferença no banco (SUM dos sale_items) comparado ao informado pelo operador.

7. Alertas, relatórios e Grafana
Criar alertas de estoque baixo (< minimum_stock) e validade (5 ou 7 dias) usando a extensão pg_cron no Supabase ou via Edge Functions agendadas, persistindo em alerts com chave de deduplicação.

Para o Grafana, criar um usuário PostgreSQL via SQL: CREATE USER grafana_reader WITH PASSWORD '...'; GRANT USAGE ON SCHEMA public TO grafana_reader; GRANT SELECT ON ALL TABLES IN SCHEMA public TO grafana_reader;.

O Grafana conectará diretamente via Pooler (Supavisor) do Supabase. Não usar APIs REST lentas. O Grafana não terá permissão de insert/update, garantindo segurança absoluta.

8. Configuração segura do cliente (Reflex)
No backend Reflex (ou .env), configurar as variáveis:

Plaintext
SUPABASE_URL=https://<seu-projeto>.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
A ANON_KEY pode ser trafegada; a segurança é dada pelo JWT emitido no login e pelo RLS do banco.

Exigir HTTPS.

Não registrar senhas ou dados sensíveis em logs.

Não confiar em preços, valores totais de venda ou cálculos de diferença de caixa enviados pelo navegador; o banco deve recalcular.

Nunca inserir a SERVICE_ROLE_KEY na camada visível do Reflex.

9. Verificação antes de produção
[ ] Todas as tabelas do schema public possuem RLS habilitado (ENABLE ROW LEVEL SECURITY).

[ ] Usuários sem sessão (sem token JWT) recebem rejeição (HTTP 401/403) ou lista vazia nas tabelas.

[ ] Operador recebe erro se tentar rodar a RPC de cancelar venda.

[ ] O banco rejeita inserção direta em inventory_movements pelo cliente (RLS fechado).

[ ] Venda consome lotes em ordem FEFO atômica (FOR UPDATE).

[ ] Venda com estoque insuficiente em 1 item cancela a transação inteira e não baixa os outros itens.

[ ] Reenvio do mesmo request_id (duplo clique) devolve a venda original, não debita duas vezes.

[ ] Lote vencido não é vendido; alertas de 5/7 dias não geram duplicação diária (deduplicação funciona).

[ ] Conexão do Grafana funciona utilizando o usuário restrito grafana_reader isolado do Reflex.

10. Operação e manutenção
Fazer alterações de schema no ambiente local de desenvolvimento do Supabase, rodando supabase db diff para gerar migrations antes de subir para produção (supabase db push).

Planejar importação de dados inicial verificando duplicidade de códigos de barra (via constraints UNIQUE).

Utilizar os backups automáticos (PITR) do Supabase para restauração em caso de acidentes severos.

Monitorar a carga do banco e ajustar os índices (B-tree) conforme a loja crescer.