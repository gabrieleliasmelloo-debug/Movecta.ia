# Validação pendente da base de conhecimento

Este arquivo não é carregado pela Movecta.IA. Ele serve como checklist para revisão humana antes de uso real.

## Conflitos identificados

1. **Vale-refeição**
   - `common/beneficios_funcionarios.md`: R$ 35,00 por dia útil.
   - `common/rh_basico.md`: R$ 45,00 por dia útil.
   - É necessário confirmar o valor oficial.

2. **Antecedência para solicitação de férias**
   - `employee/processos_funcionarios.md`: mínimo de 30 dias.
   - `common/rh_basico.md`: 45 dias.
   - É necessário confirmar a política oficial.

3. **Portal interno**
   - Há referências diferentes, como `movecta.intranet.com.br` e `movecta.intranet`.
   - Confirmar o endereço real antes de disponibilizar o agente.

4. **Contatos de RH**
   - Há referências a `rh@movecta.com.br`, ramal `1234` e ao nome de um gerente de RH.
   - Confirmar quais dados são reais e quais são placeholders do protótipo.

## Conteúdo jurídico

O arquivo `common/normas_clt.md` contém referências datadas e simplificações jurídicas. Exemplo: salário mínimo identificado como valor de 2024. Antes de uso em produção:

- atualizar valores e datas;
- revisar afirmações jurídicas com fonte oficial;
- separar claramente política interna de obrigação legal;
- evitar usar esse arquivo como substituto de orientação jurídica.

## Benefícios e políticas

Diversos benefícios, valores, prazos e programas parecem ter sido criados para teste do protótipo. Eles devem ser validados pelo RH antes de qualquer implantação para colaboradores.

## Recomendação

Até a validação final, tratar toda a pasta `knowledge_base` como **base de demonstração**.
