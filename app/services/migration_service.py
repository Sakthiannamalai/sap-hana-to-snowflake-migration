import json

import openai


from app.config import get_env_variable
from app.utils import logger, convert_timestamp_to_timestamp_tz


openai.api_key = get_env_variable("API_KEY")


async def convert_view_into_snowflake(xml):
    VIEW_PROMPT = (
        f"""
           Objective:
               You need to convert an SAP HANA calculation view (represented as XML) into an optimized Snowflake SQL stored procedure. The procedure should generate views for each type of ProjectionView, and CTEs for JoinView, AggregationView, and RankView, while maintaining the exact order and dependencies defined in the XML.
               Conditions:
                   1. Stored Procedure Creation:
                       1.1 Create a stored procedure named as described in the description tag of the XML.
                       1.2 The procedure should take any necessary parameters (based on the XML) and return a table of the final results.
                   2.Views: Inside the store procedure,
                       2.1 For every calculation view of type Calculation:ProjectionView or ProjectionView, create a corresponding Snowflake view.
                       2.2 These views should be created using CREATE OR REPLACE VIEW statements based on the SQL logic in the SAP HANA XML.
                   3. CTEs: Inside the store procedure,
                       3.1 Create separate Common Table Expressions (CTEs) for the following calculation view types:
                           Calculation:JoinView
                           Calculation:AggregationView
                           Calculation:RankView
                       3.2 Each CTE should be handled separately and not combined in a single WITH clause.
                       3.3 For each <mapping> element, if the source and target names differ, use the source AS target syntax to ensure accurate aliasing in the SQL views and CTEs.
                           Example: If source="CodeName" and target="Product Code", write it as CodeName AS ProductCode in the SELECT statement.
                   4. Result Set:
                       4.1 The final result should be returned using the RETURN TABLE(res) syntax.
                       4.2 Ensure the data types are correctly mapped to Snowflake types (e.g., VARCHAR, NUMBER, DATE).
                   5.Order of Execution:
                       5.1 Follow the exact order defined in the XML to ensure consistency and logic flow.
                   6.AvoidDefault Client And Language:
                       6.1 In the Calculation:scenario, avoid including the defaultClient='$$client$$' and defaultLanguage='$$language$$' attributes in the converted SQL. These attributes should not be included in the Snowflake SQL code.
                   7.Function Usage Guidelines:
                       7.1.Verify that all custom or unsupported functions in SAP HANA are replaced by Snowflake equivalents.
                            Example mappings:
                                NOT ISNULL(expression) → expression IS NOT NULL
                                ISNULL(expression, replacement) → IFNULL(expression, replacement)
                                COALESCE(expression, ...) → COALESCE(expression, ...)
                                NVL(expression, replacement) → IFNULL(expression, replacement)
                                NOT ISNULL() -> IS NOT NULL
                                TO_DATE() → TO_TIMESTAMP() or CAST()

               --Example Stored Procedure Creation:
               CREATE OR REPLACE PROCEDURE YourProcedureName(
                   param1 DATA_TYPE1,
                   param2 DATA_TYPE2,
                   ...
               )
               RETURNS TABLE (
                   column1 DATA_TYPE1,
                   column2 DATA_TYPE2,
                   ...
               )
               LANGUAGE SQL
               AS
               $$
               DECLARE
                   res RESULTSET;
               BEGIN

                   CREATE OR REPLACE VIEW projection_view1 AS
                   SELECT
                       column1 AS column1_name,
                       column2 AS column2_name
                   FROM source_table;

                   CREATE OR REPLACE VIEW projection_view2 AS
                   SELECT
                       column1 AS column1_name,
                       column2 AS column2_name
                   FROM source_table2;

                   WITH sample_join_cte AS (
                       SELECT
                           a.column1 AS col_a,
                           b.column2 AS col_b
                       FROM projection_view1 a
                       JOIN projection_view2 b
                           ON a.column1 = b.column2
                   ) SELECT * FROM sample_join_cte;

                   CREATE OR REPLACE VIEW projection_view3 AS
                   SELECT
                       col_a,
                       col_b
                   FROM sample_join_cte;

                   WITH sample_agg_cte AS (
                       SELECT
                           col_a,
                           COUNT(*) AS count_column
                       FROM projection_view3
                       GROUP BY col_a
                   ) SELECT * FROM sample_agg_cte;

                   CREATE OR REPLACE VIEW projection_view4 AS
                   SELECT
                       col_a,
                       count_column
                   FROM sample_agg_cte;

                   WITH sample_rank_cte AS (
                       SELECT
                           col_a,
                           count_column,
                           RANK() OVER (PARTITION BY col_a ORDER BY count_column DESC) AS rank_col
                       FROM projection_view4
                   ) SELECT * FROM sample_rank_cte;

                   CREATE OR REPLACE VIEW projection_view5 AS
                   SELECT
                       col_a,
                       count_column,
                       rank_col
                   FROM sample_rank_cte;

                   res := (
                       SELECT
                            col_a AS column1,
                           count_column AS column2,
                           rank_col AS column3
                       FROM projection_view5
                   );

                   -- Return the result set
                   RETURN TABLE(res);

               END;
               $$;
               Input SAP HANA XML: {xml}
               **Output Format**:
                   Your response should be in strict JSON format, as shown below:
                       ```json {{"sql": "<converted Snowflake SQL code here>" }}```
        """
    )
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # Use the most appropriate engine
        messages=[
            {"role": "system", "content": "You are a highly experienced "
                                          "SAP HANA and Snowflake expert."},
            {"role": "user", "content": VIEW_PROMPT}
        ],
        max_tokens=4128,  # Adjust as needed
        temperature=0.5
    )

    response_text = response.choices[0].message['content'].strip()
    json_start_index = response_text.find('{')
    json_end_index = response_text.rfind('}') + 1

    if json_start_index != -1 and json_end_index != -1:
        json_text = response_text[json_start_index:json_end_index]
    else:
        logger.error("Failed to find JSON part in the response.")
    try:
        json_response = json.loads(json_text)
        view = json_response.get("sql")
        return f"{view}"
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return None


async def convert_schema_to_snowflake(hana_schema):
    SCHEMA_PROMPT = f"""
        Convert the following SAP HANA table schema into a Snowflake table schema.

        ### Input:
        SAP HANA Table Schema: {hana_schema}

        ### Instructions:
        - Analyze the provided SAP HANA table schema.
        - Convert it to an equivalent Snowflake table schema while maintaining the functionality and structure.
        - Ensure proper syntax for Snowflake SQL.
        - Strictly adhere to the specified JSON output format.

        ### Required Output Format:
        Your response should strictly follow the JSON format as shown below:
        ```json
        {{
            "sql": "<converted Snowflake SQL code here>"
        }}
    """

    # OpenAI API call to convert schema using GPT-4
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a highly experienced "
                                          "SQL conversion expert."},
            {"role": "user", "content": (
                f"You are an expert in both SAP HANA and Snowflake. {
                    SCHEMA_PROMPT}"
            )}
        ],
        max_tokens=1024,  # Adjust token count if necessary
        temperature=0.0  # Set to 0.0 for more deterministic results
    )

    logger.info("Response fetched successfully", response)

    response_text = response.choices[0].message['content'].strip()
    json_start_index = response_text.find('{')
    json_end_index = response_text.rfind('}') + 1

    if json_start_index != -1 and json_end_index != -1:
        json_text = response_text[json_start_index:json_end_index]
    else:
        logger.error("Failed to find JSON part in the response.")
    try:
        json_response = json.loads(json_text)
        converted_table = convert_timestamp_to_timestamp_tz(
            json_response.get("sql"))
        return f"{converted_table}"
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return None


def convert_function_to_snowflake(hana_function):
    FUNCTION_PROMPT = f"""
            Convert a SAP HANA function or procedure into a Snowflake function or procedure using SQL. Follow these steps:

            1. Identify whether the given input is a SAP HANA function or procedure.
            2. If it is a function, strictly follow the Snowflake function syntax and replicate the exact functionality defined in the SAP HANA function.
            3. Do not include unnecessary semicolons in the SQL code.

            **Example Template for Snowflake Function Conversion:**
            -- Create the Snowflake function
            CREATE OR REPLACE FUNCTION <SNOWFLAKE_FUNCTION_NAME>(<input_parameters>)
            RETURNS <return_type>
            LANGUAGE SQL
            AS
            $$
                -- Converted logic in Snowflake SQL
                <translated_expression>
            $$;

            Input SAP HANA XML: {hana_function}
                **Output Format**:
                    Your response should be in strict JSON format, as shown below:
                        ```json {{"sql": "<converted Snowflake SQL code here>" }}```
        """
    # OpenAI API call to convert schema using GPT-4
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # Specify GPT-4 model
        messages=[
            {"role": "system", "content": "You are a highly experienced "
                                          "SQL conversion expert."},
            {"role": "user", "content": (
                f"You are an expert in both SAP HANA and Snowflake. {
                    FUNCTION_PROMPT}"
            )}
        ],
        max_tokens=1024,  # Adjust token count if necessary
        temperature=0.0  # Set to 0.0 for more deterministic results
    )

    logger.info("Response fetched successfully", response)

    # Extract and clean up the response text
    response_text = response.choices[0].message['content'].strip()
    logger.info("Response Text", response_text)

    # Remove any non-JSON parts of the response
    # Example of cleaning up the response:
    # Remove the introductory text and isolate the JSON
    json_start_index = response_text.find('@@')
    json_end_index = response_text.rfind('##')

    if json_start_index != -1 and json_end_index != -1:
        json_text = response_text[json_start_index + 2:json_end_index]
    else:
        logger.error("Failed to find JSON part in the response.")
        return None
    json_text = "{" + json_text
    json_text = json_text + "}"
    # json_fin_string = sanitize_json_str   ing(json_text)
    try:
        json_response = json.loads(json_text)
        function = json_response.get("sql")

        if str.lower(
                json_response.get("is_func")) == "yes":
            return f"{function}"
        else:
            return f"{function}"
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return None
