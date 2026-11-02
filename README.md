# Solu-ao-mercadinho

## Desenvolvimento local

Use Python 3.14 com a versão atual do Reflex. Python 3.15 não é compatível com o
Reflex `0.8.28.post1` usado neste projeto.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure `SUPABASE_URL` e `SUPABASE_ANON_KEY` no arquivo `.env` antes de iniciar
a aplicação:

```powershell
reflex run
```

Para executar os testes:

```powershell
python -m unittest discover -s tests -v
```

## Hub de dashboards

A página inicial (`/`) apresenta os quatro atalhos de relatórios. Os relatórios
de vendas diárias e semanais usam Plotly e consultam compras concluídas em
`public.purchases`, filtrando `created_at`. O acesso de leitura para os
relatórios é limitado aos perfis proprietário e gerente pela política RLS em
`supabase/migrations/20261102180000_allow_admin_sales_reports.sql`; aplique as
migrações Supabase do projeto antes de usar esses gráficos.

Os cards de estoque abrem `/estoque-baixo` e `/data-proxima`. Os indicadores
usam os lotes de `public.stock_lots`: estoque baixo considera até 10 unidades
somadas em lotes ainda válidos; validade próxima mostra lotes com unidades
disponíveis que vencem entre hoje e os próximos 15 dias.

## Documentação do projeto

- [Domain Model — Sistema de Gestão do Mercadinho](<docs/Domain Model — Sistema de Gestão do Mercadinho.md>)
- [Project Overview — Sistema do Mercadinho](<docs/Project Overview — Sistema do Mercadinho.md>)
- [Guia de configuração do Xano](<docs/Xano Setup — Sistema do Mercadinho.md>)
- [Cutover Supabase e migração de dados do Xano](docs/supabase-cutover-and-xano-data-migration.md)