-- =====================================================================
-- QUERY 2 - Funcionarios por Regiao (com localizacao)
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
-- Salvar o arquivo como data/query_02.csv
--
-- OBJETIVO
-- Analisar salarios e distribuicao geografica dos funcionarios,
-- percorrendo toda a cadeia de localizacao da empresa.
--
-- JOINS UTILIZADOS (4 LEFT JOIN)
-- A cadeia geografica do esquema HR e indireta: o funcionario nao possui
-- endereco proprio. A localizacao vem do departamento onde ele trabalha:
--
--   EMPLOYEES -> DEPARTMENTS -> LOCATIONS -> COUNTRIES -> REGIONS
--
--   1. HR.DEPARTMENTS -> setor e LOCATION_ID
--   2. HR.LOCATIONS   -> cidade e estado/provincia
--   3. HR.COUNTRIES   -> pais
--   4. HR.REGIONS     -> macro-regiao (Europe, Americas, Asia, ...)
--
-- CONSEQUENCIA IMPORTANTE DESSA CADEIA
-- Como a localizacao depende do departamento, o funcionario que nao possui
-- departamento tambem fica sem cidade, pais e regiao. Com LEFT JOIN ele
-- permanece no resultado com esses campos nulos - o que torna a lacuna
-- explicita.
-- Este e o motivo pelo qual esta consulta retorna 107 linhas, mas apenas
-- 106 possuem regiao preenchida. A diferenca entre esses dois numeros e
-- um achado da analise, nao um erro.
--
-- FILTRO
-- Mesma decisao da Query 1: "SALARY IS NOT NULL" preserva a distribuicao
-- completa. Filtrar por "REGION_NAME IS NOT NULL" descartaria exatamente
-- o registro que evidencia a falha de cadastro.
--
-- NOTA DE DIALETO (Oracle)
-- Concatenacao usa "||" - o CONCAT do Oracle aceita apenas 2 argumentos.
-- =====================================================================

SELECT
    e.EMPLOYEE_ID                       AS ID_FUNCIONARIO,
    e.FIRST_NAME || ' ' || e.LAST_NAME  AS FUNCIONARIO,
    d.DEPARTMENT_NAME                   AS DEPARTAMENTO,
    l.CITY                              AS CIDADE,
    l.STATE_PROVINCE                    AS ESTADO_PROVINCIA,
    c.COUNTRY_NAME                      AS PAIS,
    r.REGION_NAME                       AS REGIAO,
    e.SALARY                            AS SALARIO
FROM HR.EMPLOYEES e
LEFT JOIN HR.DEPARTMENTS d ON e.DEPARTMENT_ID = d.DEPARTMENT_ID
LEFT JOIN HR.LOCATIONS   l ON d.LOCATION_ID   = l.LOCATION_ID
LEFT JOIN HR.COUNTRIES   c ON l.COUNTRY_ID    = c.COUNTRY_ID
LEFT JOIN HR.REGIONS     r ON c.REGION_ID     = r.REGION_ID
WHERE e.SALARY IS NOT NULL
ORDER BY r.REGION_NAME, c.COUNTRY_NAME, e.SALARY DESC;
