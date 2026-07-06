/** Hisobchi Bot — Railway deploy (inventarizatsiya asosiy, mesta dublikatni o'chiradi) */

const TOKEN = (process.env.RAILWAY_TOKEN || "").trim();
if (!TOKEN) {
  console.error("RAILWAY_TOKEN yo'q");
  process.exit(1);
}

const API = "https://backboard.railway.com/graphql/v2";

const PROJECT = {
  projectId: "07249ace-db4b-44c1-8545-f1a5f1ea29cc",
  environmentId: "f7c5c3ad-6ea3-454d-8416-f1121cf04292",
};

const INV = { ...PROJECT, serviceId: "1309ba4f-7493-4f52-87f4-b7ec982e77e4", label: "inventarizatsiya" };
const MESTA = { ...PROJECT, serviceId: "9143549c-56c5-4160-aedb-026a757d61f3", label: "mesta-dup" };

const SYNC_KEYS = [
  "BOT_TOKEN",
  "GROUP_CHAT_ID",
  "ADMIN_IDS",
  "DATABASE_URL",
  "YORDAMCHI_HUB_URL",
  "YORDAMCHI_HUB_SECRET",
  "YORDAMCHI_BOT_TOKEN",
  "YORDAMCHI_INGEST_CHAT_ID",
];

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

async function getVars(serviceId) {
  const data = await gql(
    `query($p:String!,$e:String!,$s:String!){ variables(projectId:$p, environmentId:$e, serviceId:$s) }`,
    { p: PROJECT.projectId, e: PROJECT.environmentId, s: serviceId }
  );
  return data.variables || {};
}

async function upsertEnv(serviceId, variables) {
  await gql(
    `mutation($input: VariableCollectionUpsertInput!) { variableCollectionUpsert(input: $input) }`,
    {
      input: {
        projectId: PROJECT.projectId,
        environmentId: PROJECT.environmentId,
        serviceId,
        variables,
        replace: false,
      },
    }
  );
}

async function deploy(serviceId, label) {
  const data = await gql(
    `mutation($s:String!,$e:String!,$latest:Boolean){ serviceInstanceDeploy(serviceId:$s, environmentId:$e, latestCommit:$latest) }`,
    { s: serviceId, e: PROJECT.environmentId, latest: true }
  );
  console.log(`deploy ${label}:`, data.serviceInstanceDeploy ? "OK" : "?");
}

async function main() {
  const mestaVars = await getVars(MESTA.serviceId);
  const invVars = await getVars(INV.serviceId);

  const sync = {
    MINUTES_PER_POSITION: invVars.MINUTES_PER_POSITION || mestaVars.MINUTES_PER_POSITION || "2",
    MINUTES_PER_POSITION_PRIHOD: "3",
    TZ: "Asia/Tashkent",
  };
  for (const k of SYNC_KEYS) {
    const v = mestaVars[k] || invVars[k];
    if (v) sync[k] = v;
  }
  if (!sync.BOT_TOKEN) {
    throw new Error("BOT_TOKEN topilmadi (mesta yoki inventarizatsiya env)");
  }

  await upsertEnv(INV.serviceId, sync);
  console.log("env inventarizatsiya: BOT_TOKEN + prihod norm sync");

  await deploy(INV.serviceId, INV.label);

  // Eski dublikat polling — tokenni olib tashlash (bitta bot ishlashi uchun)
  await upsertEnv(MESTA.serviceId, { BOT_TOKEN: "" });
  console.log("mesta-dup: BOT_TOKEN tozalandi (dublikat polling oldini olish)");
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
