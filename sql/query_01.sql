-- =====================================================================
-- QUERY 1 - Salario por Departamento e Cargo
--
-- Projeto: Analise Exploratoria da Estrutura Salarial e Distribuicao
--          Geografica - Esquema HR
-- Aluno:   Leo Gobel
-- Turma:   Visualizacao de Dados e Business Intelligence - T2
--
-- ONDE EXECUTAR
-- FreeSQL (https://freesql.com/) - Oracle Database 26ai
-- Navigator > selecionar o esquema "Human Resources (HR)"
-- Colar esta consulta no [SQL Worksheet], executar (F5 ou botao Run) e
-- exportar o resultado em Query result > Download > CSV.
-- Salvar o arquivo como data/query_01.csv
--
-- OBJETIVO
-- Analisar a distribuicao dos salarios por departamento e por cargo,
-- trazendo tambem a faixa salarial (banda) definida pela empresa para
-- cada cargo, o percentual de comissao e o gestor direto.
--
-- JOINS UTILIZADOS (3 LEFT JOIN)
--   1. HR.DEPARTMENTS -> nome do setor
--   2. HR.JOBS        -> titulo do cargo e banda salarial (MIN/MAX)
--   3. HR.EMPLOYEES m -> auto-relacionamento para obter o nome do gestor
--
-- POR QUE LEFT JOIN E NAO INNER JOIN
-- Existe um funcionario com DEPARTMENT_ID nulo. Com INNER JOIN esse
-- registro sumiria da analise sem qualquer aviso, e a folha de pagamento
-- ficaria incompleta. O LEFT JOIN preserva os 107 funcionarios e deixa o
-- departamento como NULL, tornando a ausencia visivel e analisavel.
--
-- POR QUE O FILTRO E "SALARY IS NOT NULL"
-- O enunciado sugeria filtros como "WHERE SALARY > 5000" ou
-- "WHERE DEPARTMENT_ID IS NOT NULL". Ambos foram descartados de forma
-- deliberada:
--   - "DEPARTMENT_ID IS NOT NULL" eliminaria justamente o registro que
--     justifica o uso do LEFT JOIN;
--   - "SALARY > X" aplicaria um corte na propria variavel que o projeto
--     se propoe a estudar. Isso trunca a cauda inferior da distribuicao,
--     comprime o IQR e altera artificialmente a contagem de outliers
--     (demonstrado no Bloco 6 da analise em Python).
-- O filtro adotado garante integridade da metrica sem enviesar a
-- distribuicao: mantem os 107 funcionarios.
--
-- NOTAS DE DIALETO (Oracle)
--   - Concatenacao usa "||". O CONCAT do Oracle aceita apenas 2
--     argumentos, entao CONCAT(nome, ' ', sobrenome) nao funcionaria.
--   - TO_CHAR formata a data como texto ISO (YYYY-MM-DD), evitando que o
--     CSV saia no formato padrao do Oracle (ex.: 07-JUN-12) e simplificando
--     a leitura no pandas.
-- =====================================================================

SELECT
    e.EMPLOYEE_ID                       AS ID_FUNCIONARIO,
    e.FIRST_NAME || ' ' || e.LAST_NAME  AS FUNCIONARIO,
    d.DEPARTMENT_NAME                   AS DEPARTAMENTO,
    j.JOB_TITLE                         AS CARGO,
    e.SALARY                            AS SALARIO,
    j.MIN_SALARY                        AS PISO_CARGO,
    j.MAX_SALARY                        AS TETO_CARGO,
    e.COMMISSION_PCT                    AS PCT_COMISSAO,
    TO_CHAR(e.HIRE_DATE, 'YYYY-MM-DD')  AS DATA_ADMISSAO,
    m.FIRST_NAME || ' ' || m.LAST_NAME  AS GESTOR_DIRETO
FROM HR.EMPLOYEES e
LEFT JOIN HR.DEPARTMENTS d ON e.DEPARTMENT_ID = d.DEPARTMENT_ID
LEFT JOIN HR.JOBS        j ON e.JOB_ID        = j.JOB_ID
LEFT JOIN HR.EMPLOYEES   m ON e.MANAGER_ID    = m.EMPLOYEE_ID
WHERE e.SALARY IS NOT NULL
ORDER BY d.DEPARTMENT_NAME, e.SALARY DESC;
