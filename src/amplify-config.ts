/**
 * AWS Amplify / Cognito config.
 * Set VITE_COGNITO_USER_POOL_ID and VITE_COGNITO_CLIENT_ID in .env (see .env.example).
 */
export const amplifyConfig = {
  Auth: {
    Cognito: {
      userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID ?? '',
      userPoolClientId: import.meta.env.VITE_COGNITO_CLIENT_ID ?? '',
    },
  },
};
