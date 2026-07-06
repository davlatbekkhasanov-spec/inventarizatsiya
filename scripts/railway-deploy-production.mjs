/** InventarizatsiyaBot (asosiy production) — Railway deploy */

const TOKEN = (process.env.RAILWAY_TOKEN || "").trim();
if (!TOKEN) {
  console.error("RAILWAY_TOKEN yo'q");
  process.exit(1);
}

const API = "https://backboard.railway.com/graphql/v2";

/** inventarizatsiya-bot / production — skrinshotdagi loyiha */
const INV = {
  projectId: "e25f2e25-5287-460a-b375-4baffb878c9e",
  environmentId: "0a45c238-55e5-4472-a75c-716d69972be9",
  serviceId: "81853696-3f18-4ea8-b261-fd480b9aebe1",
};

async function gql(query, variables = {}) {
  const res = await fetch(API, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query, variables }),
  });
  const data = await res.json();
  if (data.errors?.length) {
    throw new Error(data.errors.map((e) => e.message).join("; "));
  }
  return data.data;
}

async function main() {
  await gql(
    `mutation($input: VariableCollectionUpsertInput!) { variableCollectionUpsert(input: $input) }`,
    {
      input: {
        projectId: INV.projectId,
        environmentId: INV.environmentId,
        serviceId: INV.serviceId,
        variables: {
          MINUTES_PER_POSITION_PRIHOD: "3",
          TZ: "Asia/Tashkent",
        },
        replace: false,
      },
    }
  );
  console.log("env: MINUTES_PER_POSITION_PRIHOD=3");

  const data = await gql(
    `mutation($s:String!,$e:String!,$latest:Boolean){
      serviceInstanceDeploy(serviceId:$s, environmentId:$e, latestCommit:$latest)
    }`,
    { s: INV.serviceId, e: INV.environmentId, latest: true }
  );
  console.log("deploy InventarizatsiyaBot:", data.serviceInstanceDeploy ? "OK" : "?");
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
