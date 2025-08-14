# 1) Seus modelos Pydantic (esqueleto)
from pydantic import BaseModel
from typing import List, Dict, Optional

class Reference(BaseModel):
    keys: List[Dict[str, str]]

class AssetInformation(BaseModel):
    assetKind: str
    globalAssetId: Optional[str] = None

class AssetAdministrationShell(BaseModel):
    id: str
    assetInformation: AssetInformation
    submodels: List[Reference] = []

class Property(BaseModel):
    idShort: str
    valueType: str
    value: str

class Submodel(BaseModel):
    id: str
    submodelElements: List[Property] = []

class Environment(BaseModel):
    assetAdministrationShells: List[AssetAdministrationShell] = []
    submodels: List[Submodel] = []
    conceptDescriptions: List[dict] = []

# 2) Criar um Environment simples
sm = Submodel(
    id="urn:example:submodel:techdata:1",
    submodelElements=[Property(idShort="temperature", valueType="double", value="23.5")]
)
aas = AssetAdministrationShell(
    id="urn:example:aas:robotarm:1",
    assetInformation=AssetInformation(assetKind="Instance"),
    submodels=[Reference(keys=[{"type":"Submodel","value":sm.id}])]
)
env = Environment(assetAdministrationShells=[aas], submodels=[sm])

# 3) Empacotar em .aasx (versão didática/simplificada p/ integrar no fluxo)
import json, zipfile, io, datetime

def write_aasx_simplified(environment: Environment, attachments: Dict[str, bytes], out_path: str):
    """
    Exemplo didático: grava environment.json e anexos dentro de um ZIP .aasx.
    Observação: isto NÃO implementa todo o OPC/relationships exigido pela especificação.
    Serve para mostrar 'onde e como' integrar a exportação. Para produção,
    implemente o empacotamento OPC (Content_Types, _rels, parts, relationships).
    """
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # JSON do Environment (sua camada de serialização controla aliases/camelCase)
        zf.writestr("aasx/environment.json", environment.model_dump_json(indent=2))
        # Exemplos de anexos (thumbnails, arquivos de dados etc.)
        for rel_path, data in attachments.items():
            zf.writestr(f"aasx/{rel_path}", data)

# 4) Uso típico (ex.: dentro de um endpoint/CLI)
write_aasx_simplified(
    env,
    attachments={"files/readme.txt": b"Sample attachment"},
    out_path="export.aasx",
)
print("AASX gerado em export.aasx")
