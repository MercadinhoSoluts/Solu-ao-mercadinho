# Guia de configuração do Xano — Sistema do Mercadinho

Este guia define a configuração do Xano como banco de dados gerenciado e backend REST do sistema. O Xano não deve ser tratado como um servidor PostgreSQL acessível diretamente pelo Reflex: leitura e gravação passam por endpoints do Xano, onde ficam as regras de negócio e as verificações de acesso.

> O workspace do Xano informado já existe. O schema descrito neste guia é o destino planejado; consulte [Estado atual da integração](#estado-atual-da-integração) antes de assumir que todas as tabelas e APIs já foram configuradas.

## Workspace informado

- Painel administrativo: [workspace do Sistema do Mercadinho](https://x8ki-letl-twmt.n7.xano.io/workspace/169507-0/database) (requer autenticação na conta Xano autorizada).
- Este link abre a interface de gerenciamento do workspace; não é uma URL de API e não deve ser usada pelo Reflex como endereço do banco.
- Para conectar a aplicação, publique os grupos de endpoints e obtenha no Xano a URL base da API e a documentação dos endpoints. Não compartilhar senha, token de autenticação ou chave administrativa no repositório ou na conversa.

## Estado atual da integração

- Workspace `169507-0`, instância `x8ki-letl-twmt.n7.xano.io`, plano Free.
- Tabelas verificadas no workspace: `user` e `event_log` (iniciais do Xano), `categories` e `products`.
- `categories` contém os campos básicos `name` e `is_active`; `products` tem cadastro básico, preço em centavos, unidade, limite de estoque, perecibilidade e estado ativo. Os campos `category_id` e `created_by` em `products` ainda são inteiros, sem referências formais configuradas; o índice de código de barras também não é único.
- Tabelas de lote, venda, item de venda, movimentação, caixa e alertas ainda não foram criadas.
- Os endpoints REST do mercadinho ainda não foram publicados e o repositório ainda não tem aplicação Reflex conectada. Portanto, o banco ainda não está integrado de ponta a ponta ao sistema.
- As tabelas criadas estão vazias; nenhum dado de teste ou credencial foi adicionado ao workspace.

## 1. Arquitetura de acesso

```text
Navegador / Reflex
       │ HTTPS + sessão do usuário
       ▼
API REST do Xano ─── regras, permissões e validações
       │
       ▼
Banco relacional gerenciado pelo Xano

Grafana ─── endpoints agregados e somente leitura do Xano
```

- O Xano é a fonte de verdade para produtos, lotes, vendas, caixa e movimentações.
- O Reflex chama a API do Xano pelo backend da aplicação. Não enviar tokens de serviço ao navegador.
- O Grafana recebe somente endpoints agregados e autorizados. Não expor credenciais administrativas nem acesso irrestrito às tabelas.
- Usar workspaces ou ambientes separados para desenvolvimento/testes e produção. Não testar importações ou baixas no ambiente de produção.

## 2. Preparação do workspace

1. Acessar o [workspace informado](https://x8ki-letl-twmt.n7.xano.io/workspace/169507-0/database) com a conta Xano autorizada; confirmar que é o workspace correto antes de fazer alterações.
2. Configurar os ambientes de desenvolvimento e produção, quando disponíveis no plano, mantendo schemas e configurações sincronizados.
3. Usar a tabela `user` existente e o mecanismo de autenticação nativo do Xano; não criar nem armazenar senhas em uma tabela própria.
4. Comparar `categories` e `products` existentes com a seção [Modelo de dados](#3-modelo-de-dados), completando campos, tipos e referências que ainda faltam.
5. Criar as tabelas restantes na ordem da seção [Modelo de dados](#3-modelo-de-dados), sem apagar as tabelas iniciais do Xano.
6. Criar grupos de endpoints para `auth`, `products`, `inventory`, `sales`, `cash`, `alerts` e `reports`.
7. Aplicar autenticação e autorização em cada endpoint conforme a [Matriz de permissões](#5-matriz-de-permissões).
8. Criar os endpoints de negócio e implementar as regras críticas no backend do Xano, não apenas no cliente Reflex.
9. Publicar os grupos de endpoints, obter a URL base da API e configurar os segredos no ambiente de execução do backend Reflex. Nunca versionar tokens.
10. Validar o fluxo de venda e FEFO usando os casos da seção [Verificação antes de produção](#9-verificação-antes-de-produção).

## 3. Modelo de dados

Use os IDs gerados pelo Xano para as chaves primárias. Configure referências de tabela nos campos indicados e índices para os campos usados em busca e filtros. Valores monetários são armazenados como inteiros em centavos; quantidades são numéricas para permitir unidades fracionadas, por exemplo, quilogramas.

| Tabela | Campos recomendados | Regras e índices |
|---|---|---|
| Usuários (tabela nativa de autenticação do Xano) | Campos nativos de autenticação; `name` (texto); `role` (enum: `operator`, `manager`, `owner`); `is_active` (booleano) | O nome físico da tabela pode ser o padrão do workspace. Não armazenar senha em campo adicional. Apenas dono/gestor autorizado pode provisionar usuários. |
| `categories` | `name` (texto); `is_active` (booleano); `created_at` (data/hora) | Nome obrigatório; índice para busca por nome. |
| `products` | `barcode` (texto, opcional); `name` (texto); `category_id` (referência a `categories`, opcional); `sale_price_cents` (inteiro); `unit` (enum: `unit`, `kg`, `g`, `l`, `ml`, `pack`); `minimum_stock` (numérico); `is_perishable` (booleano); `is_active` (booleano); `created_by` (referência a usuários); `created_at` (data/hora) | Preço e limite de estoque não negativos. Código de barras único quando informado. Indexar código de barras e nome. |
| `lots` | `product_id` (referência a `products`); `expiration_date` (data, opcional para item sem validade); `quantity_received` (numérico); `quantity_remaining` (numérico); `received_at` (data/hora); `created_by` (referência a usuários) | Quantidades não negativas; validade obrigatória para perecíveis. Indexar `product_id`, validade e saldo para consulta FEFO. |
| `sales` | `operator_id` (referência a usuários); `status` (enum: `completed`, `cancelled`); `payment_method` (enum: `cash`, `card`, `pix`); `total_cents` (inteiro); `request_id` (texto/UUID); `created_at` (data/hora); `cancelled_at` (data/hora, opcional) | `request_id` único para idempotência. Total não negativo. Venda cancelada não deve apagar o histórico. |
| `sale_items` | `sale_id` (referência a `sales`); `product_id` (referência a `products`); `quantity` (numérico); `unit_price_cents` (inteiro); `subtotal_cents` (inteiro) | Quantidade positiva. Guardar preço praticado na venda, sem recalculá-lo a partir do preço atual do produto. Indexar `sale_id`. |
| `inventory_movements` | `product_id` (referência a `products`); `lot_id` (referência a `lots`); `sale_id` e `sale_item_id` (referências opcionais); `type` (enum: `purchase`, `bulk_entry`, `sale`, `damage`, `loss`, `correction`, `cancellation_reversal`); `quantity` (numérico positivo); `direction` (enum: `in`, `out`); `reason` (texto, opcional); `created_by` (referência a usuários); `created_at` (data/hora) | Todo movimento de estoque identifica um lote, inclusive produtos sem validade. Registro de auditoria: não permitir alteração ou exclusão por endpoints comuns. Toda alteração de saldo gera movimentação. |
| `cash_sessions` | `opened_by` e `closed_by` (referências a usuários); `status` (enum: `open`, `closed`); `opening_cash_cents` (inteiro); `expected_cash_cents`, `counted_cash_cents`, `difference_cents` (inteiros, opcionais até fechamento); `opened_at`, `closed_at` (data/hora); `notes` (texto, opcional) | No máximo uma sessão aberta por caixa/loja. Se houver mais de um caixa, acrescentar identificador do terminal. Diferença calculada no backend, não confiada ao cliente. |
| `alerts` | `type` (enum: `low_stock`, `expiring_lot`, `cash_anomaly`); `priority` (enum: `low`, `medium`, `high`); `message` (texto); `product_id`, `lot_id` (referências opcionais); `status` (enum: `open`, `resolved`, `dismissed`); `deduplication_key` (texto); `due_date` (data, opcional); `created_at`, `resolved_at` (data/hora opcionais) | A chave única identifica uma ocorrência (tipo, entidade e janela/data); ao surgir uma nova ocorrência após resolução, gerar nova chave. Indexar status e tipo. |

### Relacionamentos

- Uma categoria pode classificar muitos produtos; a categoria de um produto pode ser opcional.
- Um produto possui muitos lotes, itens de venda e movimentações.
- Uma venda pertence a um operador e possui muitos itens de venda.
- Cada item referencia um produto. As movimentações de saída associadas aos itens identificam os lotes consumidos pelo FEFO.
- Uma sessão de caixa tem operador de abertura e, se encerrada por outra pessoa, operador de fechamento.
- Um alerta pode referenciar um produto, um lote ou ambos, conforme o tipo.

### Estoque e histórico

`lots.quantity_remaining` é o saldo disponível do lote usado para decidir se uma venda pode ser concluída. `inventory_movements` é o histórico imutável que permite auditar como o saldo mudou. Toda operação de entrada, venda, avaria, perda, correção autorizada ou reversão deve atualizar o saldo do lote e registrar a movimentação na mesma operação de backend.

Não permitir que a interface altere `quantity_remaining` diretamente. Uma correção de inventário deve ser registrada como movimentação com motivo e usuário responsável.

## 4. Contratos iniciais dos endpoints

Os caminhos abaixo são nomes lógicos para organizar os endpoints no Xano; o prefixo e a URL final são fornecidos pelo workspace. Defina os tipos de entrada e saída no Xano e mantenha-os estáveis para os clientes.

| Método e caminho lógico | Acesso | Uso |
|---|---|---|
| `POST /auth/login` | Público, com limite de tentativas | Autenticar usuário e iniciar sessão. |
| `GET /auth/me` | Usuário autenticado | Retornar identidade, papel e estado da conta do usuário atual. |
| `GET /products` | Autenticado | Listar produtos ativos, com paginação e busca. |
| `GET /products/by-barcode/{barcode}` | Autenticado | Localizar item para leitura no PDV. |
| `POST /products` / `PATCH /products/{id}` | Conforme papel | Criar/editar cadastro, validando código de barras e campos. |
| `POST /inventory/receipts` | Operador, gestor ou dono | Registrar entrada de um ou mais lotes, associada a produtos. |
| `POST /inventory/adjustments` | Gestor ou dono | Registrar avaria, perda ou correção com justificativa e auditoria. |
| `GET /inventory/summary` | Autenticado | Retornar saldo disponível por produto e indicadores de estoque baixo. |
| `POST /sales/checkout` | Operador, gestor ou dono | Validar, registrar venda, consumir estoque FEFO e criar movimentações. |
| `GET /sales` / `GET /sales/{id}` | Conforme papel | Consultar vendas, com filtros e paginação; ocultar dados não autorizados. |
| `POST /sales/{id}/cancel` | Gestor ou dono | Cancelar segundo política explícita, com reversão auditável. |
| `POST /cash-sessions/open` / `POST /cash-sessions/{id}/close` | Conforme papel | Abrir ou fechar caixa; calcular valores esperados no backend. |
| `GET /alerts` | Conforme papel | Consultar alertas abertos e seu nível de prioridade. |
| `GET /reports/sales-summary` | Gestor ou dono | Retornar totais agregados por período para relatórios e dashboards. |
| `GET /reports/dashboard` | Dono ou serviço autorizado | Retornar indicadores agregados, sem expor dados desnecessários. |

### Exemplo de solicitação de venda

O cliente envia identificadores de produto e quantidades, não os subtotais nem o saldo desejado. O backend resolve preço vigente, disponibilidade, lotes FEFO e total:

```json
{
  "request_id": "7f2e2a10-81de-4f64-9c56-40c48fb6b770",
  "payment_method": "pix",
  "items": [
    { "product_id": 123, "quantity": 2 },
    { "product_id": 456, "quantity": 0.5 }
  ]
}
```

Uma resposta de sucesso deve conter o identificador da venda, status, total em centavos, itens com preços praticados e comprovante/recibo necessário ao PDV. Repetir a mesma solicitação com o mesmo `request_id` deve retornar o resultado já registrado, sem criar outra venda nem debitar estoque novamente.

As respostas de erro devem distinguir, pelo menos: produto inexistente/inativo, quantidade inválida, estoque insuficiente, forma de pagamento inválida, usuário sem permissão e falha interna. Não retornar sucesso se qualquer etapa obrigatória da venda falhar.

## 5. Matriz de permissões

Aplicar as permissões dentro de cada endpoint do Xano. Ocultar botões no Reflex é uma conveniência de interface, não uma barreira de segurança.

| Ação | Operador | Gestor | Dono |
|---|:---:|:---:|:---:|
| Consultar produtos e registrar venda | Sim | Sim | Sim |
| Cadastrar produto, registrar entrada/lote ou avaria | Sim | Sim | Sim |
| Fazer correção de saldo e cancelar venda | Não | Sim | Sim |
| Consultar fechamento e relatórios financeiros | Não | Sim | Sim |
| Abrir/fechar sessão de caixa | Sim | Sim | Conforme política da loja |
| Consultar dashboard e alertas operacionais | Sim | Sim | Sim |
| Gerenciar usuários e papéis | Não | Conforme política da loja | Sim |

Criar usuários de forma controlada e atribuir papéis no backend. Não aceitar um `role` enviado pelo cliente como autoridade para conceder permissões.

## 6. Regras de negócio obrigatórias no backend

### Finalização de venda e FEFO

Implementar `POST /sales/checkout` como uma única operação de negócio no servidor:

1. Autenticar o usuário, validar seu papel e validar o formato da solicitação.
2. Consultar primeiro o `request_id`; se a tentativa já foi concluída, retornar a venda existente.
3. Validar produtos ativos, quantidades positivas, formas de pagamento e saldo total disponível.
4. Ordenar lotes disponíveis por validade crescente; consumir primeiro os lotes com vencimento mais próximo. Para lotes sem validade, aplicar uma ordenação determinística posterior aos lotes com validade.
5. Calcular preços, subtotais e total no backend; criar venda e itens com o preço unitário praticado.
6. Atualizar saldo dos lotes e registrar uma movimentação de saída por produto/lote consumido.
7. Marcar a venda como concluída e só então retornar sucesso.

As gravações da venda, itens, saldos e movimentações precisam ser atômicas. Antes de produção, confirme que a configuração do workspace Xano consegue aplicar a operação transacional necessária a todas essas alterações e proteger atualizações concorrentes do saldo. A verificação de idempotência também deve estar dentro da operação protegida para evitar duplicação por solicitações simultâneas. Se não for possível garantir atomicidade, reversão segura e proteção contra concorrência, não colocar o fluxo em produção. Validar com testes concorrentes que duas vendas não consumam o mesmo saldo.

### Outras regras

- Calcular estoque baixo pela soma de saldos não vencidos dos lotes de produtos ativos, comparada a `minimum_stock`.
- Gerar alertas de vencimento para perecíveis nos prazos definidos pela loja (5 ou 7 dias), ignorando lotes sem saldo e vencidos; evitar duplicidade pela chave de deduplicação.
- Registrar toda baixa/entrada em `inventory_movements`, com usuário, data/hora e origem.
- Não apagar vendas finalizadas. Cancelamentos devem ser autorizados, auditados e gerar reversões de estoque conforme a política de negócio, sem apagar os movimentos originais.
- Calcular divergência de caixa no backend usando vendas por forma de pagamento e dados de abertura/fechamento; não aceitar valores calculados pelo cliente como fonte de verdade.
- Definir explicitamente se venda de produto vencido é bloqueada. Até essa decisão ser configurada, o fluxo de venda não deve considerar lote vencido como disponível.

## 7. Alertas, relatórios e Grafana

- Criar alertas de estoque baixo e validade por endpoint/tarefa agendada do Xano, persistindo o estado em `alerts` para consulta pela interface.
- Para Grafana, criar endpoints dedicados com agregações por dia/semana, estoque baixo, perdas e alertas. Retornar apenas campos necessários; usar um conector HTTP compatível ou uma camada de integração segura, conforme a infraestrutura adotada.
- Usar credencial de serviço de privilégio mínimo, somente leitura, e restringir endpoints de relatório aos dados da loja.
- Não conectar Grafana diretamente ao banco gerenciado do Xano nem publicar token administrativo em datasource, painel ou configuração versionada.
- Definir intervalos de atualização compatíveis com os limites da API; dashboards não devem consultar tabelas linha a linha em cada atualização.

## 8. Configuração segura do cliente

No backend Reflex, configurar a URL base e o token aplicável por ambiente usando variáveis de ambiente ou o mecanismo de secrets do provedor de execução. Nomes sugeridos:

```text
XANO_API_BASE_URL=
XANO_SERVICE_TOKEN=
```

O nome da variável não cria o segredo: configurar valores no ambiente de desenvolvimento/deploy e nunca preencher valores reais no repositório. A aplicação de usuário deve preferir a identidade/sessão individual para chamadas autenticadas; usar token de serviço somente em operações servidor-servidor justificadas.

- Exigir HTTPS.
- Não registrar senhas, tokens, cabeçalhos `Authorization` ou dados de pagamento em logs.
- Aplicar limites de requisição e paginação nos endpoints.
- Não confiar em identificadores de usuário, papel, preço, total ou quantidade de estoque recebidos como valores calculados pelo navegador.
- Rotacionar/revogar tokens expostos e limitar seu escopo.

## 9. Verificação antes de produção

- [ ] Usuários sem sessão não acessam endpoints privados.
- [ ] Operador não consegue executar ações exclusivas de gestor/dono chamando a API diretamente.
- [ ] Código de barras duplicado é rejeitado; código ausente pode ser tratado conforme a regra de cadastro.
- [ ] Entrada de lote registra saldo e movimento; quantidade negativa ou zero é rejeitada.
- [ ] Venda consome lotes em ordem FEFO, incluindo venda atendida por mais de um lote.
- [ ] Venda com estoque insuficiente não altera vendas, itens, saldos nem movimentos.
- [ ] Reenvio de `request_id` não duplica venda nem baixa.
- [ ] Duas vendas concorrentes não deixam saldo negativo.
- [ ] Lote vencido não é vendido; alertas de 5/7 dias são deduplicados.
- [ ] Cancelamento gera auditoria e reversão conforme a política definida.
- [ ] Fechamento de caixa calcula valores esperados no backend e registra divergência.
- [ ] Endpoints de dashboard retornam somente agregados autorizados.
- [ ] Tokens não estão em arquivos versionados, logs, navegador ou painéis Grafana.
- [ ] Exportação/backup e procedimento de restauração foram testados antes de carregar o inventário real.

## 10. Operação e manutenção

- Manter uma cópia/exportação de segurança do workspace e dados conforme os recursos disponíveis no plano do Xano; testar restauração periodicamente.
- Fazer alterações de schema primeiro no ambiente de desenvolvimento, atualizar os contratos e validar os clientes antes de publicar em produção.
- Planejar importação inicial de produtos e lotes com validação, deduplicação por código de barras e conferência de totais antes de habilitar o PDV.
- Monitorar erros e limites de API. Alertar a equipe quando endpoints críticos falharem ou a integração ficar indisponível.
- Documentar mudanças de campos, enums e endpoints para que Reflex, Grafana e Xano permaneçam compatíveis.
