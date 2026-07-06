/** Inventarizatsiya (Hisobchi Bot) — Railway deploy + prihod env */

const TOKEN = (process.env.RAILWAY_TOKEN || "").trim();
if (!TOKEN) {
  console.error("RAILWAY_TOKEN yo'q");
  process.exit(1);
}

const API = "https://backboard.railway.com/graphql/v2";

const INV = {
  projectId: "07249ace-db4b-44c1-8545-f1a5f1ea29cc",
  environmentId: "f7c5c3ad-6ea3-454d-8416-f1121cf04292",
  serviceId: "1309ba4f-7493-4f52-87f4-b7ec982e77e4",
};

const MESTA = {
  projectId: "07249ace-db4b-44c1-8545-f1a5f1ea29cc",
  environmentId: "f7c5c3ad-6ea3-454d-8416-f1121cf04292",
  serviceId: "9143549c-56c5-4160-aedb-026a757d61f3",
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

async function upsertEnv({ projectId, environmentId, serviceId, variables }) {
  const q = `mutation($input: VariableCollectionUpsertInput!) {
    variableCollectionUpsert(input: $input)
  }`;
  await gql(q, {
    input: { projectId, environmentId, serviceId, variables, replace: false },
  });
}

async function deploy({ serviceId, environmentId, label }) {
  const q = `mutation($serviceId: String!, $environmentId: String!, $latestCommit: Boolean) {
    serviceInstanceDeploy(serviceId: $serviceId, environmentId: $environmentId, latestCommit: $latestCommit)
  }`;
  const data = await gql(q, { serviceId, environmentId, latestCommit: true });
  console.log(`deploy ${label}:`, data.serviceInstanceDeploy ? "OK" : "?");
}

async function main() {
  const env = {
    MINUTES_PER_POSITION_PRIHOD: "3",
    TZ: "Asia/Tashkent",
  };

  await upsertEnv({ ...INV, variables: env });
  console.log("env inventarizatsiya: MINUTES_PER_POSITION_PRIHOD=3");

  await upsertEnv({ ...MESTA, variables: env });
  console.log("env mesta: MINUTES_PER_POSITION_PRIHOD=3");

  await deploy({ serviceId: INV.serviceId, environmentId: INV.environmentId, label: "inventarizatsiya" });
  await deploy({ serviceId: MESTA.serviceId, environmentId: MESTA.environmentId, label: "mesta-nazorat-bot" });
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
