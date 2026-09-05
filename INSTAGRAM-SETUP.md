# Instagram API setup

## 1. What this is for

A Netlify function on this site calls Instagram's API (Instagram API with Instagram Login, for Business and Creator accounts) to pull Rad's recent posts. That call needs a long lived access token stored in the Netlify environment variable INSTAGRAM_ACCESS_TOKEN. The function refreshes that token itself every week so nobody has to repeat this process manually once it is set up.

## 2. One-time setup

1. Register as a Meta developer and create an app in the Meta App Dashboard. The app must be a Business type app: "If your current Meta app type is not a Business type app you will need to create a new app and select Business during the creation process."
   https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login

2. In the app, add the Instagram product: "Instagram > Instagram API setup with Facebook login" (this is the setup path the docs describe for adding Instagram to the app).
   https://developers.facebook.com/docs/instagram-platform/overview

3. You (Erik) will need the app's Instagram App ID and App Secret from the Meta App Dashboard. The docs list these as prerequisites for the login flow: "Instagram App ID and App Secret from Meta App Dashboard."
   https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login

4. Confirm the account type: this API requires the Instagram account to be a Business or Creator (professional) account, not a Personal account. The docs frame the whole API around "Instagram API with Instagram Login" for these account types.
   https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/

5. NEEDS RAD: Rad must log into Instagram once, on the account itself, to authorize the app. This happens during the "Generate token" flow below (step 2 in section 3), not as a separate step. Rad does not need to touch the Meta App Dashboard or Netlify at any point, only the Instagram login screen at that one moment.
   https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login

6. The permission scope the function needs to read media is instagram_business_basic. The docs list four current scopes and mark this one as the "foundational access" scope:
   instagram_business_basic, instagram_business_content_publish, instagram_business_manage_messages, instagram_business_manage_comments. Only instagram_business_basic is needed to read /me/media.
   https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/

7. Note on access level: the docs distinguish "Advanced Access (for third party accounts) or Standard Access (for owned accounts)." Since Rad's own account is what is being connected, Standard Access is the relevant tier: "Standard Access is intended for apps that will only be used by people who have roles on them, during app development, or for testing your app."
   https://developers.facebook.com/docs/instagram-platform/overview

## 3. How to generate the long lived token

The docs describe a dashboard button flow for this, so use it instead of the manual OAuth exchange:

1. "In your app dashboard, click Instagram > API setup with Instagram business login in the left side menu."
   https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login

2. "Click Generate token next to the Instagram account you want to access." This is the step where Rad logs in: "Log into Instagram." (This is the login moment referenced in step 5 above.)
   https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login

3. "Copy the access token." The docs do not name what this token is called on screen beyond "access token"; the docs do not name this control beyond "Generate token" and "Copy the access token."
   https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login

If the dashboard button ever does not produce a long enough lived token, the documented manual path is:
- Authorize at https://www.instagram.com/oauth/authorize with client_id, redirect_uri, response_type=code, and scope=instagram_business_basic. This returns an authorization code valid for one hour.
- Exchange that code for a short lived token with a POST to https://api.instagram.com/oauth/access_token using client_id, client_secret, grant_type=authorization_code, redirect_uri, and the code from the previous step.
- Exchange the short lived token for a long lived one (valid 60 days) with a GET to https://graph.instagram.com/access_token using grant_type=ig_exchange_token, client_secret, and the short lived token from the previous step.
  https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login

4. Once you have the token (from step 3 above, the "Copy the access token" step), go to the Netlify dashboard: Site configuration then Environment variables. Add a variable named INSTAGRAM_ACCESS_TOKEN with the value [value from step 3], and set it to "Same value for all deploy contexts."

## 4. What the function does afterward

The token from step 3 is valid for 60 days. The Netlify function refreshes it weekly using the refresh endpoint: "GET https://graph.instagram.com/refresh_access_token" with grant_type=ig_refresh_token and the current access_token. The docs require the token to be "at least 24 hours old but has not expired" for this call to succeed, and the refreshed token is "valid for 60 days from the refresh date." A weekly refresh schedule stays comfortably inside both bounds.
https://developers.facebook.com/docs/instagram-platform/reference/refresh_access_token

If the Instagram account is ever switched from Business or Creator back to Personal, this stops working, since the whole API is scoped to "Instagram API with Instagram Login" for professional account types; the docs do not describe a personal account variant of this flow.
https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/

## 5. Things the docs say can break it

- Wrong app type: the app must be Business type from creation; the docs are explicit that a non Business app cannot be converted in place and a new app is required instead.
  https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login

- Refreshing too soon: a refresh call on a token less than 24 hours old will not work, per the "at least 24 hours old" requirement above.
  https://developers.facebook.com/docs/instagram-platform/reference/refresh_access_token

- Refreshing too late: if the token expires before a refresh happens, the docs indicate the refresh only works on a token that "has not expired," so an expired token needs the full re-authorization in section 3 again, including Rad logging in again.
  https://developers.facebook.com/docs/instagram-platform/reference/refresh_access_token

- Wrong scope: only instagram_business_basic is granted or the deprecated older scopes are used. The docs warn: "The old scope values will be deprecated on January 27, 2025," so any setup still using pre-2025 scope names needs to move to instagram_business_basic and the other instagram_business_* scopes.
  https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/

- Access level: the docs distinguish Standard Access (people with a role on the app) from Advanced Access (third party accounts) as a possible source of permission errors depending on which tier the app is set to.
  https://developers.facebook.com/docs/instagram-platform/overview

- Account type: the docs do not describe a fallback for Personal accounts; the whole flow assumes Business or Creator.
  https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/

The docs consulted did not include a page describing development mode versus live mode limits or tester role assignment for this specific product; if the token generation step in the dashboard fails with a permissions error, check the app's mode and role assignments directly in the Meta App Dashboard, since the docs do not name this control beyond generic App Dashboard navigation.
