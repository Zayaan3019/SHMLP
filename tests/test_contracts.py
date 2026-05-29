import pandas as pd

from shmlrp.data.schema import default_schema


def test_schema_contract_fails_on_missing_column() -> None:
    df = pd.DataFrame({"feature_1": [1.0], "target": [0]})
    schema = default_schema()
    result = schema.validate(df)
    assert not result.is_valid
    assert any("Missing column" in issue for issue in result.issues)
