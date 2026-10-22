# Cutover Supabase e migração de dados do Xano

## Estado atual

O aplicativo Reflex usa Supabase Auth, PostgREST, a Edge Function
`employee-management` e as funções de estoque do PostgreSQL. O uso de Xano em
tempo de execução foi removido dos fluxos de autenticação, funcionários,
produtos e estoque. A tela de preços agora usa o histórico de preços do
Supabase em vez de dados simulados.

Os arquivos `xano/table/*.xs` disponíveis são definições de esquema, não
exportações de registros. Não há uma exportação autenticada dos dados do Xano
neste workspace. Portanto, **a migração dos dados e o cutover permanecem
pendentes**. Não reintroduza registros do Xano manualmente sem exportação,
validação e reconciliação.

A política local da Edge Function agora permite que `manager` e `owner`
gerenciem os mesmos cargos. A função já implantada não foi atualizada nesta
etapa; execute os testes Deno e implante a versão revisada antes de considerar
essa paridade ativa no projeto vinculado.

Na última inspeção somente de leitura do projeto Supabase vinculado, havia um
perfil proprietário ativo e nenhum produto, lote de estoque, movimento de
estoque ou histórico de preços. Esses valores são apenas a linha de base
observada; confira novamente antes de importar. Nenhuma importação ou escrita
de dados foi realizada.

## Escopo e mapeamento

Fluxos usados pelo aplicativo e destino:

| Xano / comportamento anterior | Supabase |
|---|---|
| Login, sessão e consulta do usuário | Supabase Auth e `public.profiles` |
| Listagem e CRUD de funcionários | Edge Function `employee-management` e Supabase Auth |
| `produtos` e lookup relacionado em `codigobarra` | `public.products` |
| Consulta e recebimento/ajuste de `estoque` | `public.stock_lots`, `public.inventory_movements`, `receive_stock` e `correct_stock` |
| Preços anteriormente mantidos em memória | `public.product_price_history` e `public.current_product_prices` |

O mapeamento de campos para uma futura importação é:

| Xano | Supabase / regra |
|---|---|
| `user.id` | Novo UUID de Supabase Auth; IDs inteiros não são reutilizados |
| `user.email`, `user.name`, `user.role`, `user.is_active` | Auth e `profiles`; contas precisam ser recriadas e senhas redefinidas |
| `user.role`: `operator` ou `caixa` | `operator` |
| `user.role`: `manager`, `admin` ou `administrador` | `manager` |
| `user.role`: `owner`, `proprietario` ou `proprietário` | `owner` |
| `produtos.id` | UUID determinístico no manifesto de validação, derivado do ID Xano |
| `produtos.nome`, `marca`, `peso` | `products.product_type`, `brand`, `weight_grams` |
| `codigobarra.produtos_id`, `codigo_de_barras` | Produto associado e `products.barcode`; o destino aceita um código por produto |
| `estoque.produtos_id`, `lote`, `unidades`, `validade` | `stock_lots.product_id`, `batch_label`, `units`, `expires_on` |
| `preco.produtos_id`, `preco_unitario`, `created_at` | `product_price_history.product_id`, `price_cents`, `created_at` |

`public.app_role` contém somente `operator`, `manager` e `owner`. Os nomes de
negócio são aliases, não rótulos adicionais do enum. `admin` e
`proprietario` têm as mesmas permissões administrativas; `caixa` mantém o
acesso operacional já aprovado para Produtos, Conferência e Estoque. Os
recursos de Caixa/PDV e Relatórios continuam sem persistência de vendas: os
endpoints Xano chamados `vendas` observados consultam ou gravam `preco` e não
são usados pelo fluxo atual da aplicação.

Não é possível transferir senhas Xano para Supabase Auth. IDs antigos de
usuários não podem ser usados como IDs de Auth. A tabela Xano `estoque` contém
saldos, não movimentos históricos; uma importação pode registrar saldos
iniciais, mas não reconstruir o histórico de movimentações. O agrupamento
atual do aplicativo combina estoque do mesmo produto e validade, mantendo o
primeiro lote; divergências nessa combinação devem ser revistas antes da
importação.

## Validar uma exportação antes da importação

Solicite exportações JSON dos registros atuais de `user`, `produtos`,
`codigobarra`, `estoque` e `preco`. Cada arquivo deve conter um array de
objetos e ser nomeado exatamente como abaixo:

```text
users.json
produtos.json
codigobarra.json
estoque.json
preco.json
```

Execute a validação local, sem conexão com o Supabase:

```powershell
python scripts\validate_xano_export.py C:\caminho\seguro\exportacao-xano `
  --output C:\caminho\seguro\manifesto-validacao.json
```

O comando retorna código diferente de zero se houver dados ausentes ou
incompatíveis, inclusive referências órfãs, e-mails duplicados, códigos de
barras sem correspondência ou duplicados, mais de um código por produto,
campos obrigatórios inválidos e valores monetários que não cabem em centavos.
O manifesto contém contagens, mapeamento determinístico de IDs de produtos,
avisos e erros; não inclui e-mails, senhas nem os registros pessoais. Ele
**não** conecta nem grava dados no Supabase e não substitui a revisão manual
dos conflitos.

## Sequência de importação e critérios de cutover

1. Obtenha uma exportação autorizada e consistente do Xano; proteja-a como
   dado pessoal e preserve uma cópia imutável da origem.
2. Execute o validador, corrija os erros na origem ou documente uma decisão
   aprovada para cada divergência. Revise especialmente códigos múltiplos,
   estoque agrupado e arredondamento de preços.
3. Confirme novamente o estado do Supabase vinculado, o histórico de migrações
   e a ausência de conflitos com UUIDs, códigos de barras e e-mails. Não faça
   importação se o estado divergir da linha de base sem reconciliação.
4. Recrie as contas via Auth/fluxo confiável de funcionários, valide cada
   perfil e distribua uma redefinição de senha. Nunca importe campos
   `password` ou tokens de recuperação do Xano.
5. Importe produtos antes de códigos de barras, estoque e preços, preservando
   os UUIDs do manifesto. Registre saldos iniciais usando uma operação
   controlada que mantenha a consistência entre lote e movimentos. Insira cada
   preço como histórico imutável com conversão exata para centavos.
6. Compare contagens e integridade referencial entre origem e destino;
   confira amostras de produtos/códigos, lotes/saldos e preços atuais. Valide
   login, permissões e os fluxos do aplicativo em ambiente aprovado.
7. Só anuncie o cutover após aprovação explícita das reconciliações e testes.
   Preserve o Xano sem novas escritas e mantenha documentada a limitação de
   rollback: gravações novas no Supabase não são sincronizadas para o Xano.

Nenhum importador com escrita remota é fornecido ou executado nesta etapa:
sem os registros de origem não é possível validar com segurança conversões,
conflitos e identidade de contas. A exportação validada e a aprovação do plano
de reconciliação são pré-requisitos para implementar/executar a carga
controlada.

## Bootstrap do primeiro proprietário

O projeto vinculado já possui um proprietário ativo; não execute o bootstrap
nele. Em um projeto novo, crie primeiro a conta Auth pelo painel confiável do
Supabase e confirme a criação do perfil. Depois, como administrador do banco
no SQL Editor, substitua o UUID de exemplo abaixo pelo ID Auth e execute uma
única vez. A operação aborta se já houver qualquer perfil `owner` ou se o
perfil indicado não existir/estiver inativo:

```sql
DO $$
DECLARE
    initial_owner_id uuid := '00000000-0000-0000-0000-000000000000';
BEGIN
    IF EXISTS (SELECT 1 FROM public.profiles WHERE role = 'owner') THEN
        RAISE EXCEPTION 'An owner profile already exists.';
    END IF;

    UPDATE public.profiles
       SET role = 'owner'
     WHERE id = initial_owner_id
       AND is_active;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'The active Auth profile was not found.';
    END IF;
END;
$$;
```

Não adicione credenciais privilegiadas ao app Reflex nem crie um endpoint
público de bootstrap.

## Migrações já registradas

O projeto vinculado já registra `20261017180000` e
`20261022000000_app_role_compatibility.sql` como aplicadas. A migração de
compatibilidade usa `normalize_app_role(text)` para converter aliases nos
três valores legados do enum. **Não marque, repare nem reaplique essas
migrações cegamente.** Confira `supabase migration list --linked` e o esquema
remoto antes de qualquer aplicação futura.
