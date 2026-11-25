# 3. Sustentar — Como mantenho o sistema no ar e recupero quando cai? {#sustentar}

Quem lê: operação e suporte · Referência: práticas ITIL

## 3.1 Deploy e infraestrutura {#s-deploy}

Hoje o banco roda na nuvem do Supabase e a aplicação roda num computador local com `reflex run`. Enquanto a hospedagem não for definida (P04), o sistema só funciona com esse computador ligado.

| Componente | Onde roda hoje | Como publicar uma mudança |
| --- | --- | --- |
| Aplicação Reflex | Computador local, porta 3000 | `git pull` na `main` e `reflex run` |
| Banco (esquema) | Supabase, projeto `jsmmzjnulxmxlprrqgcn`, us-east-1, plano gratuito | `supabase link --project-ref jsmmzjnulxmxlprrqgcn` e `supabase db push` |
| Edge Function | Supabase, versão 11 ativa | `supabase functions deploy employee-management` |
| Segredos da função | Cofre de segredos do Supabase | `supabase secrets set NOME=valor` |

- **Infraestrutura como código:** o esquema inteiro está nas migrações e em `supabase/config.toml`; um projeto novo é recriado com `supabase db push`.
- **CI/CD:** não há pipeline de deploy. O único workflow do GitHub prepara o ambiente do Copilot. Publicar ainda é manual.
- **Modelo de operação desta entrega:** a aplicação roda num computador do mercado, ligado durante o expediente, e o banco fica na nuvem do Supabase. O computador precisa de internet, Python 3.14 e do projeto instalado conforme a aba Manter (2.6).
- **Próximo passo de hospedagem:** publicar no Reflex Cloud com `reflex deploy`, para que o sistema funcione sem depender desse computador. A publicação é feita pela equipe assim que o cliente aprovar o custo (P04).

## 3.2 Runbooks {#s-runbooks}

| Incidente | Como aparece | O que fazer |
| --- | --- | --- |
| App não sobe | `reflex run` termina com erro de Python | Confirme a branch `main` (`git status`), rode `git pull` e reinstale as dependências. `SyntaxError` indica código quebrado na branch atual |
| App lento ou Git não troca de branch | Mensagem "Deletion of directory … failed" | Pause a sincronização do OneDrive ou mova o projeto para fora dele |
| Ninguém consegue entrar | Login falha para todos | Abra o painel do Supabase: projetos gratuitos podem ser pausados por inatividade; reative o projeto |
| Erro "schema do Supabase não corresponde" | Mensagens com `PGRST202`, `PGRST204` ou `PGRST205` | Migrações faltando no banco: rode `supabase db push` |
| Cadastro de funcionário falha com erro 5xx | Tela Cadastro mostra falha do servidor | Confira se a função está ativa e se os segredos estão definidos; republique a função |
| Operador não consegue iniciar venda | Compra anterior ficou aberta | Cada operador só tem uma compra aberta: finalize ou cancele a pendente |
| Saldo de lote errado | Estoque não bate com a prateleira | Corrigir com `correct_stock`, como gerente e com motivo; ainda não há tela |

**Reiniciar:** `Ctrl+C` no terminal e `reflex run` de novo. Nenhum dado se perde, porque tudo fica no Supabase.

**Rollback:** no app, volte para o commit anterior (`git checkout <commit>`) e reinicie. No banco, nunca edite uma migração aplicada: crie uma nova que desfaça a anterior e aplique com `supabase db push`.

## 3.3 Monitoramento {#s-monitoramento}

Não há alertas automáticos configurados. O acompanhamento é feito nos painéis abaixo.

| O que acompanhar | Onde ver | O que significa | Frequência sugerida |
| --- | --- | --- | --- |
| Estoque baixo e validade próxima | Tela Relatórios | Alertas do negócio: repor ou retirar produto | Diária |
| Vendas diárias e semanais | Tela Relatórios | Queda brusca pode indicar caixa parado | Diária |
| Uso de API, autenticação e banco | Supabase → Reports | Próximo dos limites do plano gratuito, o serviço pode ser limitado | Semanal |
| Erros da Edge Function | Supabase → Edge Functions → Logs | Falhas no cadastro de funcionários | Ao surgir reclamação |
| Avisos de segurança e desempenho | Supabase → Advisors | Políticas faltando, índices, configurações de Auth | Após cada migração |

## 3.4 Matriz de suporte e SLA {#s-suporte}

Atendimento da MercadinhoSoluts durante os 30 dias de garantia, contados a partir do aceite da entrega. Depois desse prazo, o suporte segue as mesmas regras mediante acordo entre as partes.

| Nível | Quem atende | O que resolve | Como acionar |
| --- | --- | --- | --- |
| N1 | Gerente do mercado | Dúvidas de uso, com o manual e o FAQ; cadastro de funcionários e produtos | Interno, no próprio mercado |
| N2 | Equipe MercadinhoSoluts | Configuração, acesso, dados incorretos, correção de estoque | E-mail mercadinhozikasoluts@gmail.com |
| N3 | Desenvolvimento: Bruno Alves (código e banco), Pedro Cunha (relatórios), Igor Cruz Carvalho (documentação) | Defeitos no código, banco e Edge Function | [Issue no repositório](https://github.com/MercadinhoSoluts/Solu-ao-mercadinho/issues), aberta pela equipe N2 |

**Escalonamento:** o N1 tenta resolver com o manual; se não conseguir, envia e-mail ao N2 descrevendo a tela, a mensagem de erro e o horário. O N2 responde dentro do prazo da prioridade e, quando o problema está no código, registra uma issue para o N3.

| Prioridade | Exemplo | Primeira resposta | Solução ou contorno |
| --- | --- | --- | --- |
| Crítica | Caixa não vende ou ninguém entra | 4 horas úteis | 1 dia útil |
| Alta | Relatório ou conferência fora do ar | 1 dia útil | 3 dias úteis |
| Média | Erro com contorno conhecido | 2 dias úteis | Próxima versão |
| Baixa | Ajuste visual ou sugestão | 5 dias úteis | Planejado no roadmap |

## 3.5 Backup e continuidade {#s-backup}

Hoje não existe cópia de segurança: o plano gratuito do Supabase não inclui backups, conforme o painel do projeto. Se o banco for perdido, vendas, estoque e cadastros não podem ser recuperados.

| Opção | Como funciona | Perda máxima de dados (RPO) | Custo |
| --- | --- | --- | --- |
| Plano Pro do Supabase (recomendada) | Backup diário automático, guardado por 7 dias, restaurável pelo painel | Até 24 horas | Assinatura mensal |
| Exportação manual | `supabase db dump` diário, guardado fora do Supabase | Até 24 horas, se feita todo dia | Sem custo; depende de disciplina |
| Nada | Situação atual | Tudo | — |

- **Meta de tempo para voltar ao ar (RTO):** 4 horas, recriando o esquema com `supabase db push` e restaurando o último backup.
- **Meta de perda máxima (RPO):** 24 horas, com o plano Pro ou com a exportação diária abaixo.
- **Plano de contingência do caixa:** se o sistema cair, anotar as vendas em papel e lançá-las depois, para que o estoque continue correto.

### Exportação manual (enquanto não houver plano Pro)

No computador com o projeto e a Supabase CLI, uma vez por dia, ao fechar o caixa:

```powershell
supabase link --project-ref jsmmzjnulxmxlprrqgcn
supabase db dump -f backup_esquema.sql
supabase db dump --data-only -f backup_dados_AAAA-MM-DD.sql
```

Guarde os arquivos fora do computador do mercado (por exemplo, numa pasta de nuvem da equipe) e mantenha pelo menos os 7 últimos. Para restaurar, aplique primeiro o esquema e depois o arquivo de dados num projeto Supabase vazio, pelo editor SQL ou pelo `psql`.

## 3.6 Segurança, LGPD e base de conhecimento {#s-seguranca}

### Acessos

O acesso é por perfil, garantido pelas telas e, principalmente, pelo RLS do banco. A chave de serviço só existe nos segredos da Edge Function. Em 25/11/2026 o verificador de segurança do Supabase apontou:

| Aviso | Avaliação | Ação |
| --- | --- | --- |
| Proteção contra senhas vazadas desligada | Risco aceito: o recurso só existe no plano Pro do Supabase | Ativar ao contratar o plano Pro; até lá vale a regra de senha forte (RN12) |
| 9 funções `SECURITY DEFINER` executáveis por usuários logados | Intencional; cada função confere o papel (ADR 005) | Manter e revisar a cada função nova |
| 2 tabelas com RLS e sem políticas | Intencional; as tabelas de idempotência ficam fechadas | Nenhuma |

### LGPD

- **Dados pessoais tratados:** nome e e-mail dos funcionários. As vendas não identificam o cliente do mercado.
- **Finalidade e base legal:** controle de acesso dos funcionários ao sistema, ligado à relação de trabalho.
- **Onde ficam:** Supabase, nos Estados Unidos. A transferência internacional deve constar no aviso de privacidade aos funcionários.
- **Exclusão:** ao desligar um funcionário, exclua-o na tela Cadastro; conta e perfil são removidos.
- **Prints e treinamentos:** use contas fictícias; nunca e-mails reais.

### Base de conhecimento (incidentes já vistos)

| Data | Problema | Causa | Solução |
| --- | --- | --- | --- |
| 13/11/2026 | `reflex run` falhou com `SyntaxError` no `bipsystem.py` | Commit quebrado na branch `seed-demo-stock` | Voltar para a `main`; corrigir a branch num commit novo |
| 13/11/2026 | Troca de branch travou na exclusão de uma pasta | OneDrive bloqueando arquivos | Responder `n` e pausar a sincronização |
| — | Reflex não instala | Python 3.15 | Usar Python 3.14 |
