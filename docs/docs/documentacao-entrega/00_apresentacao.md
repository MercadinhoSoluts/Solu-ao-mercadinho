# Apresentação {#apresentacao}

## Identificação da entrega {#identificacao}

A MercadinhoSoluts entrega ao Mercadinho do Seu João o BipSystem 1.0.0, sistema web de gestão de estoque, preços e frente de caixa.

| Item | Informação |
| --- | --- |
| Fornecedor | MercadinhoSoluts |
| Cliente | Mercadinho do Seu João |
| Sistema | BipSystem — Automação Comercial |
| Versão entregue | 1.0.0 |
| Data da entrega | 13/11/2026 |
| Código-fonte | [github.com/MercadinhoSoluts/Solu-ao-mercadinho](https://github.com/MercadinhoSoluts/Solu-ao-mercadinho) (branch `main`) |
| Banco de dados | Projeto Supabase `jsmmzjnulxmxlprrqgcn`, região us-east-1, PostgreSQL 17 |
| Garantia | 30 dias após a entrega, licença definitiva sem mensalidade |
| Equipe | Bruno Alves, Pedro Cunha e Igor Cruz Carvalho (responsabilidades abaixo) |

### Equipe e responsabilidades

A divisão abaixo segue o histórico de commits do repositório.

| Integrante | Responsabilidade principal | Entregas no repositório |
| --- | --- | --- |
| Bruno Alves | Desenvolvimento (back-end, front-end e banco) | Migração para o Supabase, caixa (PDV), preços, cadastro de funcionários, menu lateral e telas principais |
| Pedro Cunha | Ambiente, relatórios e dashboards | Ambiente inicial do projeto, início da troca do Xano pelo Supabase, relatórios de vendas e responsividade |
| Igor Cruz Carvalho | Especificação e documentação | API de cadastro de funcionários no Xano, especificação no OpenSpec e esta documentação |

**Contato da equipe:** mercadinhozikasoluts@gmail.com · **Chamados técnicos:** [issues do repositório](https://github.com/MercadinhoSoluts/Solu-ao-mercadinho/issues)

### Histórico do documento

| Versão | Data | Alteração |
| --- | --- | --- |
| 1.2 | 25/11/2026 | Tratamento definido para cada item conhecido (nenhum em aberto); telas do caixa com item incluído e escolha do pagamento |
| 1.1 | 25/11/2026 | Campos pendentes preenchidos: equipe e responsabilidades, contatos de suporte, responsáveis pelas pendências, plano de operação e de backup; banco reconferido |
| 1.0 | 13/11/2026 | Primeira edição, baseada no código da `main`, no banco Supabase em produção e nas telas do sistema |

## Resumo executivo {#resumo}

O BipSystem substitui as planilhas do mercado por um sistema único: o caixa registra a venda, o estoque baixa sozinho pelo lote que vence primeiro, e o dono acompanha vendas, estoque baixo e validades num painel.

- **Pronto e em produção:** login por perfil, cadastro de funcionários, produtos e preços, entrada de mercadoria por lote e validade, frente de caixa com quatro formas de pagamento e relatórios.
- **Banco conferido em 25/11/2026:** as 6 migrações do repositório estão aplicadas, a Edge Function de funcionários está ativa e as 9 tabelas têm controle de acesso por perfil (RLS).
- **Risco aceito, com mitigação:** o plano gratuito do Supabase não faz backup. Até a contratação do plano Pro, a mitigação é a exportação diária descrita na aba Sustentar (3.5).

## Como esta documentação está organizada {#organizacao}

Cada aba responde a uma pergunta de um leitor diferente. Ninguém precisa ler tudo: o dono e os operadores ficam na aba Usar; quem vai mexer no código ou manter o sistema no ar vai para as demais.

| Aba | Pergunta que responde | Quem lê | Referência |
| --- | --- | --- | --- |
| [1. Usar](#usar) | Como faço meu trabalho com o sistema? | Sr. João, gestora, operadores | ISO/IEC/IEEE 26514 |
| [2. Manter](#manter) | Como o sistema funciona e por que foi feito assim? | Desenvolvedores | ISO/IEC/IEEE 42010 |
| [3. Sustentar](#sustentar) | Como mantenho o sistema no ar e recupero quando cai? | Operação e suporte | Práticas ITIL |
| [4. Evoluir](#evoluir) | Como atualizo sem quebrar? | Arquitetura e líder técnico | ISO/IEC/IEEE 14764 |

## Estado da entrega e pendências {#pendencias}

O sistema funciona de ponta a ponta. Nenhum item está em aberto: cada um foi resolvido, está em execução, foi decidido pela equipe, aceito como risco ou agendado para a versão 1.1.

| ID | Pendência | Impacto | Responsável | Tratamento |
| --- | --- | --- | --- | --- |
| P01 | Plano gratuito do Supabase não faz backup; mitigação: exportação diária (seção 3.5) até a contratação do plano Pro | Perda do banco sem recuperação | Cliente escolhe o plano; Bruno Alves implanta | Risco aceito |
| P02 | Por decisão de projeto (ADR 006), um gerente pode atribuir o papel de proprietário, inclusive a si mesmo; o cliente deve confirmar se aceita | Elevação indevida de acesso | Cliente decide; Bruno Alves ajusta, se preciso | Decisão de projeto |
| P03 | Proteção contra senhas vazadas desligada: o recurso só existe no plano Pro do Supabase; a regra de senha forte de 12 caracteres (RN12) reduz o risco | Senhas fracas conhecidas são aceitas | Bruno Alves | Risco aceito |
| P04 | A versão 1.0 opera localmente; a hospedagem (proposta: Reflex Cloud) fica para depois da entrega | Sistema só funciona com a máquina ligada | Cliente aprova o custo; Bruno Alves publica | Fora do escopo da 1.0 |
| P05 | Gráficos de vendas mostram a série "Semana passada (mock)", com dado fictício | Comparação semanal não confiável | Pedro Cunha | Agendada para a 1.1 |
| P06 | Dados antigos do Xano não são importados: o design da migração registrou a decisão de começar do zero no Supabase | Histórico anterior fora do sistema | Igor Cruz Carvalho | Não se aplica |
| P07 | Arquivo `.env` publicado no repositório público (contém só a URL e a chave pública) | Boa prática violada | Bruno Alves | Em andamento |
| P08 | Lote vencido aparece na tela Estoque sem destaque | Operador pode achar que há produto vendável | Bruno Alves | Agendada para a 1.1 |
| P09 | Total do caixa exibido como `0,00 R$`; o padrão brasileiro é `R$ 0,00` | Inconsistência visual | Bruno Alves | Agendada para a 1.1 |
| P10 | Prints de compra finalizada, compra cancelada, erros do caixa e login ainda faltam no manual | Manual incompleto | Igor Cruz Carvalho | Em andamento |

## Critérios de aceite da documentação {#aceite}

A documentação só é considerada entregue quando passa nos três testes abaixo.

| Critério | Como verificar | Situação |
| --- | --- | --- |
| Teste do estranho | Alguém de fora da equipe sobe o ambiente e publica o sistema seguindo só as abas Manter e Sustentar | Em andamento |
| Docs as code | Exportar este documento em Markdown para a pasta `docs/` do repositório e atualizá-lo no mesmo pull request de cada mudança | Aberta |
| Transferência de conhecimento | Sessão gravada de passagem com o cliente, seguindo o roteiro de treinamento da aba Usar, com as perguntas registradas | Aberta |
