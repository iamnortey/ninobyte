# Example 002: Code Review Output

Demonstrates the structured code review output format.

---

## User Input

```
Mode: Code Review

Review this Express.js authentication middleware:

```javascript
// auth.js
const jwt = require('jsonwebtoken');

const authMiddleware = (req, res, next) => {
  const token = req.headers.authorization;

  if (!token) {
    return res.status(401).json({ error: 'No token provided' });
  }

  try {
    const decoded = jwt.verify(token, 'my-secret-key-123');
    req.user = decoded;
    next();
  } catch (err) {
    console.log('Auth failed for token: ' + token);
    res.status(401).json({ error: 'Invalid token' });
  }
};

module.exports = authMiddleware;
```
```

---

## Expected Output

```markdown
## Code Review: auth.js (Authentication Middleware)

### Summary
**Request Changes** — The middleware has critical security issues that must be addressed before use in production. The core logic is correct, but secrets handling and logging practices need immediate fixes.

### What's Good
- Clear, focused single responsibility
- Proper use of try/catch for JWT verification
- Returns appropriate 401 status codes
- Attaches decoded user to request for downstream use

### Issues

#### 🔴 Critical (Must Fix)

**Hardcoded JWT Secret** — Line 10
```javascript
const decoded = jwt.verify(token, 'my-secret-key-123');
```
Problem: JWT secret is hardcoded in source code. This is a critical security vulnerability—anyone with code access can forge valid tokens.

Suggestion:
```javascript
const decoded = jwt.verify(token, process.env.JWT_SECRET);
```
Also add validation at startup:
```javascript
if (!process.env.JWT_SECRET) {
  throw new Error('JWT_SECRET environment variable is required');
}
```

---

**Logging Sensitive Token** — Line 15
```javascript
console.log('Auth failed for token: ' + token);
```
Problem: Logging JWT tokens exposes credentials in logs. Tokens can be replayed, and log systems may not be secure.

Suggestion:
```javascript
console.error('Auth failed: Invalid token attempt', {
  ip: req.ip,
  path: req.path,
  timestamp: new Date().toISOString()
});
```
Log contextual info, never the token itself.

---

#### 🟡 Important (Should Fix)

**Missing Bearer Prefix Handling** — Line 5
```javascript
const token = req.headers.authorization;
```
Problem: Standard JWT auth uses "Bearer <token>" format. This code would fail with standard clients or include "Bearer " in the token string.

Suggestion:
```javascript
const authHeader = req.headers.authorization;
if (!authHeader || !authHeader.startsWith('Bearer ')) {
  return res.status(401).json({ error: 'No token provided' });
}
const token = authHeader.split(' ')[1];
```

---

**No Token Expiration Handling** — Line 10
```javascript
const decoded = jwt.verify(token, 'my-secret-key-123');
```
Problem: If tokens don't have expiration or if expiration isn't enforced, tokens remain valid indefinitely.

Suggestion: Ensure tokens include `exp` claim and verify handles it (jwt.verify does this by default if claim exists). Consider adding explicit check:
```javascript
if (decoded.exp && Date.now() >= decoded.exp * 1000) {
  return res.status(401).json({ error: 'Token expired' });
}
```

---

#### 🔵 Minor (Consider)

**Generic Error Message** — Line 16
```javascript
res.status(401).json({ error: 'Invalid token' });
```
Consider: For debugging (non-production), distinguishing between expired vs malformed vs invalid signature can help. In production, generic is fine for security.

---

**No Rate Limiting Mentioned** — General
Consider: Authentication endpoints should have rate limiting to prevent brute force attacks. This middleware doesn't handle it (may be handled elsewhere).

---

### Security Considerations
- 🔴 **CRITICAL**: Hardcoded secret must be moved to environment variable
- 🔴 **CRITICAL**: Token logging must be removed
- Consider adding request rate limiting
- Consider token refresh mechanism for long-lived sessions

### Testing
- No tests visible for this middleware
- Recommend tests for:
  - Valid token → passes with user attached
  - Missing token → 401
  - Invalid token → 401
  - Expired token → 401
  - Malformed header → 401

### Questions
1. Is there a token refresh mechanism elsewhere?
2. What claims are expected in the token payload?
3. Is this middleware used with rate limiting?
```

---

## Key Behaviors Demonstrated

1. **Clear verdict** — "Request Changes" with summary
2. **Acknowledges positives** — Not just criticism
3. **Severity categorization** — Critical, Important, Minor
4. **Line-specific feedback** — Exact locations cited
5. **Code suggestions** — Not just problems, but solutions
6. **Security focus** — Prioritizes security issues
7. **Testing recommendations** — Notes missing coverage
8. **Clarifying questions** — Identifies what needs context
