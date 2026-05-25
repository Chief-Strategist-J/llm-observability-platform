Contract Tests — Handler Against Published Contract

The contract test reads the feature's contracts/v1.yaml or v1.graphql.
It verifies that the handler accepts every input the contract says it accepts.
It verifies that the handler returns every response field the contract declares.
It verifies that every error code the contract declares is returned in the correct scenario.
It verifies that required fields are enforced and optional fields work without being provided.
The service is mocked — this test is about the contract surface, not the business logic.
A contract test failure means the implementation diverges from the contract — this blocks merge.
