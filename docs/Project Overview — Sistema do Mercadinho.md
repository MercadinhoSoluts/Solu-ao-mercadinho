Project Overview — Sistema do Mercadinho

1. Visão geral

O Sistema do Mercadinho é uma plataforma de gestão integrada e inteligente desenvolvida para modernizar a operação de balcão (PDV), o controle de estoque em tempo real e a análise financeira de um mercado de bairro, substituindo controles visuais e planilhas manuais por alertas automáticos e dashboards em tempo real.

2. Problema

Atualmente, o mercado enfrenta fortes gargalos operacionais e financeiros provocados pelo controle manual (que inclui mais de 2.000 folhas de cálculo em Excel) e pela falta de automação:

Ruptura de estoque: falta frequente de produtos essenciais de alto giro (ex.: cerveja e carvão) nos dias de maior movimento (finais de semana e feriados), resultando em vendas perdidas.

Perda por validade: produtos perecíveis (com destaque para carnes, que possuem margens apertadas de 15% a 20%) vencem na prateleira antes de serem vendidos por falta de monitoramento.

Descontrole manual e vulnerabilidade: fechamento de caixa demorado e sem precisão, ausência de relatórios financeiros e exposição a erros humanos ou quebras de caixa.

3. Objetivos

Transformar a gestão da loja e reduzir prejuízos operacionais imediatos, permitindo:

Automatizar o controle de estoque com baixa em tempo real a partir das vendas do caixa.

Eliminar perdas por validade com alertas visuais preventivos baseados no método FEFO.

Otimizar o atendimento ao cliente com um sistema de frente de caixa (PDV) ágil com leitor de código de barras.

Centralizar a tomada de decisões em dashboards simples e relatórios automáticos sem burocracia.

4. Público-alvo e usuários

Operador (o sobrinho): responsável por cadastros em massa, entrada de mercadorias, registro de lotes com data de validade e gestão de avarias.

Gestora (a esposa do Sr. João): responsável por conferir o fechamento de caixa diário, analisar balanços de vendas e emitir relatórios financeiros.

Dono (Sr. João): usuário focado em visualizar alertas operacionais e indicadores no dashboard interno da loja para tomadas de decisão rápidas.

5. Escopo

O escopo do projeto contempla o ciclo completo: entrada em massa de produtos, gestão de estoque e lotes, frente de caixa (PDV) com baixa automática, emissão de comprovantes e sistema de alertas/dashboards operacionais e financeiros em tempo real.

O projeto possui garantia de 30 dias após a entrega e opera sob modelo de licença definitiva (sem mensalidades/SaaS).

6. Principais funcionalidades

MVP

Entrada e Cadastro de Mercadorias: inventário inicial, cadastro de novos produtos e importação de adição em massa.

Controle de Lotes e Validade (FEFO): registro de datas de vencimento e alertas visuais emitidos a 5 ou 7 dias do vencimento.

Frente de Caixa (PDV): interface rápida com suporte a leitor de código de barras, registro de pagamentos (cartão, Pix, dinheiro), geração de recibo e baixa automática no estoque.

Monitoramento de Ruptura: alertas automáticos para produtos de alto giro com estoque abaixo do limite estabelecido.

Dashboards e Alertas (Grafana): painel interno centralizado com relatórios diários/semanais de vendas, saúde financeira e notificações de anomalia no caixa ou estoque.

7. Requisitos e restrições importantes

Ninguém precisará aprender o sistema inteiro: a interface e os acessos são estritamente delimitados pelo papel de cada operador.

A baixa de estoque deve ser instantânea ao concluir a venda no caixa.

O dashboard interno precisa emitir alertas visuais diretos na loja para fácil compreensão do proprietário.

O investimento total é fixo em R$ 8.000,00, com ROI estimado entre 6,5 e 9 meses.

8. Arquitetura tecnológica

Ambiente de Desenvolvimento: VS Code com OpenSpec, Python/Pylance e Git Graph.

Frontend / Interface: Reflex Framework (interface reativa desenvolvida em Python).

Backend e Banco de Dados: Supabase (banco relacional PostgreSQL, APIs REST auto-geradas via PostgREST, Edge Functions e Triggers). A aplicação deve acessar os dados pelo SDK do Supabase ou via chamadas REST autenticadas, aproveitando as políticas de segurança direto no banco.

Visualização e Alertas: Grafana (dashboards analíticos, relatórios e emissão de alertas em tempo real).

O modelo de dados, os contratos iniciais das APIs e o procedimento de configuração estão documentados no Guia Supabase Tutorial: Como Criar o Backend do seu App com IA em Minutos [2026] | Marfin Blog.

9. Princípios de desenvolvimento

Seguir o fluxo OpenSpec para proposição de specs antes do código.

Desenvolver interfaces com UX/UI minimalista, simples e limpa para eliminar tempo de treinamento.

Garantir alta performance no PDV para zerar a formação de filas no balcão.

10. Segurança e integridade

Regras de controle de acesso rigorosas no backend aplicadas nativamente no banco de dados através de RLS (Row Level Security) vinculadas aos perfis de operação.

Integridade relacional no banco PostgreSQL (Supabase) para assegurar acurácia nas baixas de estoque, registros de caixa e relatórios financeiros.

O Reflex e o Grafana consomem o SDK/endpoints do Supabase; chaves administrativas (Service Role Keys) ficam somente no backend ou em Edge Functions isoladas, nunca no navegador do cliente.

Vendas, itens, lotes e movimentações devem ser gravados por operações validadas, com idempotência, Triggers para baixa automática e proteção contra estoque negativo.

11. Estratégia de desenvolvimento

Divisão clara de papéis na equipe técnica:

Pedro: responsável por Frontend, UI/UX (Reflex Framework) e criação dos dashboards/alertas visuais (Grafana).

Igor: responsável por Engenharia de Software, regras de negócio e fluxos contínuos.

Bruno: responsável por Banco de Dados (Supabase), modelagem PostgreSQL, políticas de segurança (RLS) e desenvolvimento de Triggers/Edge Functions.

O desenvolvimento será incremental, iniciando pelo inventário/cadastro e fluxo do PDV até a consolidação dos dashboards de análise.

12. Fonte de verdade e documentação

Este documento estabelece o escopo e as diretrizes estratégicas do projeto. O Guia de configuração do Supabase registra o modelo inicial de dados e as permissões esperadas. Mapeamentos de fluxos específicos, alterações futuras dos schemas do Supabase e componentes visuais no Reflex devem ser documentados via OpenSpec e diretrizes de UI.