# Users API

This project implements a serverless REST API for managing user records with AWS Lambda, API Gateway, DynamoDB, and Amazon Cognito. The API is defined by the SAM template in [template.yaml](template.yaml) and uses a Lambda token authorizer to validate Cognito-issued JWTs.

## Overview

- Base path: `/users`
- Primary runtime: Python 3.14
- Data store: Amazon DynamoDB
- Authentication: Amazon Cognito + API Gateway Lambda authorizer
- Deployment model: AWS SAM / Serverless Application Model

## Authentication

All API requests must include a valid Cognito ID token in the `Authorization` header.

Example:

```http
Authorization: <cognito-id-token>
```

Authorization behavior:

- Authenticated users can access their own resource paths: `/users/{userid}`
- Users in the `apiAdmins` Cognito group can also access the collection endpoints (`GET /users`, `POST /users`, and administrative updates/deletes)

## Endpoints

| Method | Path | Description | Access |
| --- | --- | --- | --- |
| GET | `/users` | List all users | Admins only |
| POST | `/users` | Create a new user | Admins only |
| GET | `/users/{userid}` | Retrieve one user by ID | Owner or admin |
| PUT | `/users/{userid}` | Create or update one user by ID | Owner or admin |
| DELETE | `/users/{userid}` | Delete one user by ID | Owner or admin |

## Request and response shapes

### Common response headers

```json
{
  "Content-Type": "application/json",
  "Access-Control-Allow-Origin": "*"
}
```

### GET /users

List all user records.

Request:

```http
GET /users
Authorization: <token>
```

Success response (`200 OK`):

```json
[
  {
    "userid": "f8216640-91a2-11eb-8ab9-57aa454facef",
    "name": "John Doe",
    "timestamp": "2026-06-24T12:34:56.789012"
  }
]
```

### POST /users

Create a new user.

Request:

```http
POST /users
Authorization: <token>
Content-Type: application/json
```

```json
{
  "name": "Jane Doe",
  "email": "jane@example.com"
}
```

Success response (`200 OK`):

```json
{
  "userid": "d3c7d1b7-2ff2-4b7d-8f32-f68f8c0efbe6",
  "name": "Jane Doe",
  "email": "jane@example.com",
  "timestamp": "2026-06-24T12:34:56.789012"
}
```

Notes:

- If `userid` is not provided in the request body, the handler generates a UUID.
- The handler always adds a `timestamp` field.

### GET /users/{userid}

Retrieve a single user record.

Request:

```http
GET /users/{userid}
Authorization: <token>
```

Success response (`200 OK`):

```json
{
  "userid": "f8216640-91a2-11eb-8ab9-57aa454facef",
  "name": "John Doe",
  "timestamp": "2026-06-24T12:34:56.789012"
}
```

If the requested item does not exist, the handler returns an empty JSON object.

### PUT /users/{userid}

Create or overwrite a user record for the provided ID.

Request:

```http
PUT /users/{userid}
Authorization: <token>
Content-Type: application/json
```

```json
{
  "name": "Updated Name"
}
```

Success response (`200 OK`):

```json
{
  "userid": "f8216640-91a2-11eb-8ab9-57aa454facef",
  "name": "Updated Name",
  "timestamp": "2026-06-24T12:34:56.789012"
}
```

### DELETE /users/{userid}

Delete a single user record.

Request:

```http
DELETE /users/{userid}
Authorization: <token>
```

Success response (`200 OK`):

```json
{}
```

## Error handling

Any exception in the Lambda handler returns a `400 Bad Request` response with a JSON error body such as:

```json
{
  "Error": "<exception message>"
}
```

## Underlying AWS resources

The application is deployed as a SAM-managed serverless stack with the following resources:

- API Gateway REST API
  - Exposes the `/users` and `/users/{userid}` routes
  - Uses a Lambda token authorizer for request validation
- AWS Lambda function `UsersFunction`
  - Handles all CRUD operations for users
  - Reads and writes to DynamoDB
- AWS Lambda function `AuthorizerFunction`
  - Validates Cognito JWTs and produces an API Gateway authorizer policy
- Amazon DynamoDB table `UsersTable`
  - Stores user items keyed by `userid`
  - Uses on-demand billing
- Amazon Cognito user pool `UserPool`
  - Issues JWTs used by the authorizer
- Amazon Cognito user pool client `UserPoolClient`
  - Supports user authentication flows
- Amazon Cognito user pool group `ApiAdministratorsUserPoolGroup`
  - Grants admin access to the collection endpoints when a user belongs to the `apiAdmins` group

## Deployment notes

After deployment with AWS SAM, the stack outputs include:

- `APIEndpoint` for the API Gateway base URL
- `UserPool` for the Cognito user pool ID
- `UserPoolClient` for the Cognito app client ID
- `CognitoLoginURL` for signing in through the hosted UI
