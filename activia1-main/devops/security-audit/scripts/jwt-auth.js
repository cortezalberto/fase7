/**
 * ZAP Authentication Script for JWT-based API
 * AI-Native MVP - Security Audit
 *
 * FIX Cortez49: JWT authentication script for authenticated endpoint scanning
 *
 * This script handles:
 * 1. Login to /api/v1/auth/token endpoint
 * 2. Extract JWT access_token from response
 * 3. Set Authorization header for subsequent requests
 *
 * Environment variables:
 *   - ZAP_TEST_USER: Test user email
 *   - ZAP_TEST_PASSWORD: Test user password
 *   - ZAP_TARGET_URL: Target API URL (default: http://localhost:8000)
 */

// Authentication function called by ZAP
function authenticate(helper, paramsValues, credentials) {
    var targetUrl = paramsValues.get("target_url") || "http://localhost:8000";
    var loginUrl = targetUrl + "/api/v1/auth/token";

    var username = credentials.getParam("username");
    var password = credentials.getParam("password");

    // Skip if no credentials provided
    if (!username || !password) {
        helper.getHttpSender().sendAndReceive(
            helper.prepareMessage()
        );
        return;
    }

    // Prepare login request (OAuth2 password flow)
    var requestBody = "grant_type=password" +
        "&username=" + encodeURIComponent(username) +
        "&password=" + encodeURIComponent(password);

    var msg = helper.prepareMessage();
    msg.setRequestHeader(
        new org.parosproxy.paros.network.HttpRequestHeader(
            org.parosproxy.paros.network.HttpRequestHeader.POST,
            new java.net.URI(loginUrl, false),
            "HTTP/1.1"
        )
    );
    msg.getRequestHeader().setHeader("Content-Type", "application/x-www-form-urlencoded");
    msg.setRequestBody(requestBody);

    // Send login request
    helper.getHttpSender().sendAndReceive(msg);

    // Parse response for access_token
    var responseBody = msg.getResponseBody().toString();

    try {
        var jsonResponse = JSON.parse(responseBody);

        if (jsonResponse.access_token) {
            // Store token in ZAP session
            var token = jsonResponse.access_token;
            helper.getCorrespondingHttpSession().setValue("jwt_token", token);

            // Log success (visible in ZAP console)
            print("[JWT-Auth] Successfully authenticated as: " + username);
            print("[JWT-Auth] Token expires in: " + (jsonResponse.expires_in || "unknown") + " seconds");
        } else {
            print("[JWT-Auth] ERROR: No access_token in response");
            print("[JWT-Auth] Response: " + responseBody.substring(0, 200));
        }
    } catch (e) {
        print("[JWT-Auth] ERROR parsing response: " + e.message);
        print("[JWT-Auth] Response status: " + msg.getResponseHeader().getStatusCode());
    }

    return msg;
}

// Get required parameters for this script
function getRequiredParamsNames() {
    return ["target_url"];
}

// Get optional parameters
function getOptionalParamsNames() {
    return [];
}

// Get credentials parameters
function getCredentialsParamsNames() {
    return ["username", "password"];
}

// HTTP sender hook - add JWT to all requests
function sendingRequest(msg, initiator, helper) {
    var token = helper.getCorrespondingHttpSession().getValue("jwt_token");

    if (token) {
        msg.getRequestHeader().setHeader("Authorization", "Bearer " + token);
    }

    return msg;
}

// Response received hook - check for token expiration
function responseReceived(msg, initiator, helper) {
    var statusCode = msg.getResponseHeader().getStatusCode();

    // If we get 401, token might be expired - clear it
    if (statusCode === 401) {
        var currentToken = helper.getCorrespondingHttpSession().getValue("jwt_token");
        if (currentToken) {
            print("[JWT-Auth] Token expired or invalid, clearing session");
            helper.getCorrespondingHttpSession().setValue("jwt_token", null);
        }
    }

    return msg;
}
