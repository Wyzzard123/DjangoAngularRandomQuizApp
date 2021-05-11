# Environments
Rename this folder to environments and set the Client IDs according to the Client ID you obtained when you registered your oauth toolkit app using /authorize.

You should set this app to "Public" and not "Confidential" so that we do not need to use the secret (since the client secret cannot be held securely on the server and would have to be given away in the API calls made by the Angular app).
