import { client } from "@repo/openapi-client/client";

const configureClient = () => {
  const baseURL = process.env.NEXT_PUBLIC_API_URL;

  client.setConfig({
    baseUrl: baseURL,
  });
};

configureClient();