# 🛒 BipSystem

Aplicação web de **automação comercial** desenvolvida em **Python + Reflex** pela **MercadinhoSoluts** para o **Mercadinho do Seu João**, centralizando gestão de estoque por lote e validade (FEFO), histórico imutável de preços, frente de caixa (PDV) e dashboards gerenciais em uma única plataforma.

---

## 📑 Sumário

- [Sobre o Projeto](#-sobre-o-projeto)
- [Perfis e Controle de Acesso](#-perfis-e-controle-de-acesso)
- [Funcionalidades](#-funcionalidades)
- [Arquitetura e Estrutura](#-arquitetura-e-estrutura)
- [Configuração e Execução Local](#-configuração-e-execução-local)
- [Manual de Utilização](#-manual-de-utilização)
- [Exemplos Práticos de Uso](#-exemplos-práticos-de-uso)
- [Limitações Conhecidas](#-limitações-conhecidas)
- [Documentação, Equipe e Suporte](#-documentação-equipe-e-suporte)

---

## 📌 Sobre o Projeto

O **BipSystem (v1.0.0)** substitui planilhas e controles manuais por um sistema integrado de ponta a ponta: o operador registra a venda no caixa, o banco baixa automaticamente o estoque pelo lote que vence primeiro (**FEFO** — *First Expired, First Out*) e a gestão acompanha vendas, estoque baixo e validades próximas em tempo real.

A aplicação separa a operação de frente de caixa das rotas administrativas e analíticas:
- **Para Operadores de Caixa:** frente de caixa dedicada com leitura de código de barras USB, quatro formas de pagamento, validação automática de lotes válidos, proteção contra duplicidade e apoio na entrada de mercadorias e cadastro de produtos.
- **Para Gerentes e Proprietário:** painel central com atalhos de gestão, administração de funcionários, catálogo de produtos, histórico imutável de preços em centavos, acompanhamento de lotes e relatórios gerenciais em Plotly.

### Tecnologias e Serviços Integrados
- **Frontend & Backend:** Python 3.14 + [Reflex](https://reflex.dev/) (`0.8.28.post1`)
- **Banco de Dados, Autenticação e API:** [Supabase](https://supabase.com/) (PostgreSQL 17 com RLS, Supabase Auth, PostgREST RPCs e Edge Function em Deno/TypeScript)
- **Dashboards e Gráficos:** [Plotly](https://plotly.com/python/)
- **Especificação e Versionamento:** OpenSpec + Git/GitHub

---

## 👥 Perfis e Controle de Acesso

O acesso exige autenticação por e-mail e senha previamente cadastrados pela gestão — não há autocadastro público nem credenciais de demonstração. As permissões são garantidas em duas camadas: proteção de rotas no servidor Reflex (`AuthState.require_*`) e políticas **Row Level Security (RLS)**, funções SQL `SECURITY DEFINER` e validação de papel na Edge Function do Supabase.

| Perfil | Responsabilidades | Permissões Principais | Restrições |
| :--- | :--- | :--- | :--- |
| **Operador de Caixa** | Atender clientes no PDV, registrar vendas, receber pagamentos e apoiar a entrada de mercadorias. | Acessar `/caixa-inicio` e `/caixa` (abrir, finalizar e cancelar vendas); consultar `/estoque`, registrar entradas em `/conferencia` e cadastrar itens em `/produtos`. | Não acessa o Painel Início (`/`), `/precos`, `/relatorios` nem `/cadastro`; só pode manter 1 compra aberta por vez. |
| **Gerente** | Conduzir a rotina operacional e administrativa do mercado (equipe, catálogo, preços, estoque e indicadores). | Acesso integral às telas de gestão: `/`, `/estoque`, `/conferencia`, `/produtos`, `/precos`, `/relatorios`, `/estoque-baixo`, `/data-proxima` e `/cadastro`. | Não opera o frente de caixa (`/caixa-inicio` e `/caixa` são exclusivos do perfil operador); não pode excluir a própria conta. |
| **Proprietário** | Gestão geral do estabelecimento (Seu João), acompanhamento operacional e controle da equipe. | Todas as permissões de gestão, relatórios, preços, estoque e administração de funcionários. | Não registra vendas diretamente no caixa (vendas devem ser feitas por um usuário com perfil operador). |

<details>
<summary><strong>🗺️ Ver Mapa Completo de Rotas por Perfil</strong></summary>

| Tela | Rota | Finalidade | Operador | Gerente / Proprietário |
| :--- | :--- | :--- | :---: | :---: |
| Login | `/login` | Autenticação no sistema | Sim | Sim |
| Bem-vindo do Caixa | `/caixa-inicio` | Tela inicial do operador para iniciar uma venda | Sim | Não |
| Caixa (PDV) | `/caixa` | Incluir itens, receber pagamento, finalizar ou cancelar | Sim | Não |
| Painel Início | `/` | Atalhos de gestão e resumo dos critérios de alerta | Não | Sim |
| Estoque | `/estoque` | Consulta de produtos por lote, quantidade e validade | Sim | Sim |
| Conferência | `/conferencia` | Entrada de mercadorias entregues pelo fornecedor | Sim | Sim |
| Produto | `/produtos` | Cadastro de novos produtos | Sim | Sim |
| Relatórios | `/relatorios` | Hub de dashboards (vendas, estoque baixo e validade) | Não | Sim |
| Estoque Baixo | `/estoque-baixo` | Detalhamento de produtos com até 10 unidades válidas | Não | Sim |
| Validade Próxima | `/data-proxima` | Detalhamento de lotes vencendo nos próximos 15 dias | Não | Sim |
| Cadastro | `/cadastro` | Criar, editar e excluir contas de funcionários | Não | Sim |
| Preços | `/precos` | Vincular novos preços e consultar preços vigentes | Não | Sim |

</details>

---

## ✨ Funcionalidades

- **Autenticação e Renovação de Sessão:** login por e-mail e senha com redirecionamento automático conforme o perfil, renovação transparente de token JWT e encerramento seguro via botão **Sair**.
- **Gestão de Funcionários:** listagem, criação, edição e exclusão de contas em `/cadastro` via Edge Function `employee-management`, exigindo senhas fortes (mínimo de 12 caracteres com maiúscula, minúscula, número e símbolo) e bloqueando autoexclusão.
- **Cadastro de Produtos:** registro por tipo, marca, peso em gramas e código de barras único (rejeita duplicidades); o nome exibido é composto automaticamente a partir desses campos (ex.: `Suco Laranja Tang 18 g`).
- **Preços com Histórico Imutável:** valores armazenados em centavos (`bigint`) para evitar erros de arredondamento; novos preços são inseridos em `product_price_history` sem sobrescrever o passado, expostos na visão `current_product_prices` e copiados no momento da venda para `purchase_items`.
- **Conferência e Estoque por Lote:** entrada de mercadorias por código de barras, lote, quantidade e validade (`receive_stock`), gerando histórico auditável em `inventory_movements` e busca por nome/código em `/estoque`.
- **Frente de Caixa (PDV) com Baixa FEFO:** leitura por leitor USB ou digitação, limite de uma compra aberta por operador, idempotência por identificador de requisição (protege contra cliques duplos ou rede instável), pagamento em **Dinheiro, Pix, Cartão de Crédito ou Débito**, baixa atômica priorizando lotes que vencem antes (nunca vende lotes vencidos) e cancelamento registrado sem alterar o estoque.
- **Hub de Dashboards e Relatórios:** gráficos **Plotly** de **vendas diárias** (por hora no dia atual) e **vendas semanais** (últimos 7 dias) consultando compras concluídas em `public.purchases` via `created_at` (acesso restrito a proprietário e gerente pela política RLS em `supabase/migrations/20261102180000_allow_admin_sales_reports.sql`), além dos cards de estoque que abrem `/estoque-baixo
