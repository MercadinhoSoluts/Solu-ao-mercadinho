Domain Model e Arquitetura — Sistema de Gestão do Mercadinho

Este documento descreve os conceitos fundamentais do domínio do Sistema de Gestão do Mercadinho e como eles se relacionam. Ele representa os conceitos do negócio e detalha a implementação técnica da infraestrutura migrada para o Supabase (substituindo o Xano), mantendo a lógica de negócio e o frontend inalterados.

Visão geral dos relacionamentos

Usuário (Operador / Gestor / Dono)
└── Operação
    ├── Produto
    │   └── Lote (validade)
    ├── Venda (PDV)
    │   └── Item de Venda
    ├── Movimentação de Estoque
    └── Alerta / Relatório


Usuário

Representa a pessoa que interage com o sistema na loja, com permissões baseadas em seu papel operacional.

Principais informações

Nome.

Papel ou cargo (Operador/Sobrinho, Gestora/Esposa, Dono/Sr. João).

Permissões de acesso.

Responsabilidade

Realizar ações no sistema de acordo com suas atribuições: cadastro e entradas (Operador), fechamento de caixa e relatórios (Gestora) ou consulta de alertas e dashboards estratégicos (Dono).

Relacionamentos

Um usuário pode registrar vários produtos, movimentações de estoque e vendas.

⚡ Implementação Supabase

Autenticação: Gerenciada nativamente pelo Supabase Auth (schema auth.users), substituindo os tokens nativos do Xano.

Tabela de Dados: Tabela public.usuarios_perfis vinculada ao auth.users.id via Foreign Key (UUID).

Segurança: Utiliza RLS (Row Level Security) do PostgreSQL para garantir que a permissão de acesso seja validada direto no banco (ex: auth.uid() = id).

Produto

Representa uma mercadoria comercializada ou gerenciada pelo mercadinho.

Principais informações

Código de barras ou identificador.

Nome do produto.

Categoria.

Preço de venda.

Unidade de medida.

Quantidade mínima para estoque baixo (regra de negócio).

Responsabilidade

Manter o cadastro base das mercadorias vendidas na loja.

Relacionamentos

Um produto possui vários lotes de estoque.

Um produto pode estar presente em vários itens de venda.

Um produto pode ser associado a alertas de estoque baixo.

⚡ Implementação Supabase

Tabela: public.produtos.

API: Requisições de CRUD que antes iam para o Xano agora utilizam o cliente @supabase/supabase-js (ex: supabase.from('produtos').select('*')).

Lote

Representa uma remessa específica de um produto recebida no estoque, com controle individual de validade.

Principais informações

Data de validade.

Quantidade de itens no lote.

Data de entrada ou recebimento.

Responsabilidade

Garantir o rastreio e o controle de validade (FEFO — First Expire, First Out) para evitar perdas em perecíveis.

Relacionamentos

Um lote pertence a um único produto.

Um lote pode gerar alertas de proximidade de vencimento.

⚡ Implementação Supabase

Tabela: public.lotes.

Relacionamento: produto_id (Foreign Key referenciando public.produtos.id).

Venda (PDV)

Representa uma transação comercial realizada no balcão de atendimento da frente de caixa.

Principais informações

Data e horário da transação.

Forma de pagamento (cartão, Pix ou dinheiro).

Valor total.

Status da venda (concluída ou cancelada).

Responsabilidade

Registrar a compra do cliente, disparar a dedução automática do estoque em tempo real e gerar o comprovante de venda.

Relacionamentos

Uma venda é realizada por um usuário (operador).

Uma venda contém um ou vários itens de venda.

⚡ Implementação Supabase

Tabela: public.vendas.

Integração: Inserções feitas via SDK do Supabase. O cálculo do valor total pode ser validado no banco para evitar manipulações no frontend.

Item de Venda

Representa cada produto unitário ou quantidade de produto adicionada a uma venda.

Principais informações

Produto.

Quantidade vendida.

Preço unitário praticado.

Responsabilidade

Vincular o produto à venda específica e calcular subtotais do atendimento.

Relacionamentos

Um item de venda pertence a uma única venda.

Um item de venda está associado a um único produto.

⚡ Implementação Supabase

Tabela: public.itens_venda.

Relacionamentos: venda_id e produto_id (Foreign Keys).

Movimentação de Estoque

Representa qualquer entrada, saída manual ou baixa automática que altera o saldo de produtos do mercado.

Principais informações

Tipo de movimentação (entrada por nota/compra, adição em massa, baixa automática de venda, avaria/perda).

Quantidade.

Data e hora da movimentação.

Responsabilidade

Manter o saldo de estoque atualizado e confiável em tempo real.

Relacionamentos

Uma movimentação de estoque está associada a um produto ou lote.

Uma movimentação pode ser disparada por uma venda no PDV.

⚡ Implementação Supabase

Tabela: public.movimentacoes_estoque.

Automação: Inserções automáticas (baixa de venda) ocorrem via PostgreSQL Triggers, retirando a necessidade de lógicas encadeadas (Function Stack) que o Xano utilizava.

Alerta e Dashboard

Representa os avisos e indicadores consolidados em tempo real para tomada de decisões rápidas.

Principais informações

Tipo de alerta (estoque baixo, proximidade de vencimento em 5 ou 7 dias, anomalia de caixa).

Mensagem e nível de prioridade.

Relatórios consolidados (diário e semanal de vendas).

Responsabilidade

Notificar problemas antes que gerem prejuízos (ruptura ou perda por validade) e fornecer visão financeira e operacional clara para os gestores.

Relacionamentos

Um alerta se refere a um produto ou lote específico.

⚡ Implementação Supabase

Tabela: public.alertas.

Dashboard em Tempo Real: Substitui o polling do Xano por Supabase Realtime, permitindo que o frontend receba os alertas no exato momento em que são criados no banco.

Regras estruturais importantes (Migração Lógica)

As lógicas que antes ficavam no motor visual do Xano (Function Stack) passam a rodar nativamente na infraestrutura do Supabase da seguinte forma:

Toda venda finalizada no PDV deve abater automaticamente o saldo do estoque no mesmo instante.

Supabase: Implementado através de um Database Trigger (PostgreSQL) atrelado à inserção na tabela itens_venda. O banco de dados faz a baixa automática assim que a requisição chega.

O produto deve ser deduzido do estoque respeitando a ordem do lote com vencimento mais próximo (FEFO).

Supabase: Dentro da Function (PL/pgSQL) acionada pelo Trigger acima, a query aplica um ORDER BY data_validade ASC nos lotes do produto vendido, garantindo a baixa no lote correto sem que o frontend precise enviar lógicas complexas.

O alerta de validade deve ser gerado prioritariamente para produtos perecíveis que estejam a 5 ou 7 dias do vencimento.

Supabase: Substitui os "Background Tasks" do Xano por uma Supabase Edge Function (escrita em TypeScript/Deno) agendada via pg_cron. Ela roda diariamente, varre a tabela de lotes e insere os avisos na tabela de alertas.