$ErrorActionPreference = 'Stop'

$folder = Split-Path -Parent $MyInvocation.MyCommand.Path
$csvPath = Join-Path $folder 'Gestion Stock V4 - Stock Complet.csv'
Add-Type -AssemblyName Microsoft.VisualBasic
$parser = New-Object Microsoft.VisualBasic.FileIO.TextFieldParser($csvPath, [Text.Encoding]::UTF8)
$parser.TextFieldType = [Microsoft.VisualBasic.FileIO.FieldType]::Delimited
$parser.SetDelimiters(',')
$parser.HasFieldsEnclosedInQuotes = $true
1..4 | ForEach-Object { [void]$parser.ReadFields() }
[void]$parser.ReadFields()
$rows = New-Object 'System.Collections.Generic.List[object]'
while (-not $parser.EndOfData) {
    $fields = $parser.ReadFields()
    if ($fields.Count -ge 26) {
        $rows.Add([PSCustomObject]@{
            eurocode = $fields[5]
            source_type = $fields[6]
            designation = $fields[7]
            quantity_current = $fields[9]
            purchase_price = $fields[11]
            public_price = $fields[10]
            place = $fields[19]
            date_exit = $fields[20]
            inventory_status = $fields[22]
            inventory_notes = $fields[23]
            inventory_state = $fields[25]
        })
    }
}
$parser.Close()

function Normalize-Key([string]$value) {
    if ([string]::IsNullOrWhiteSpace($value)) { return '' }
    $normalized = $value.Trim().ToUpperInvariant().Normalize([Text.NormalizationForm]::FormD)
    $chars = foreach ($char in $normalized.ToCharArray()) {
        if ([Globalization.CharUnicodeInfo]::GetUnicodeCategory($char) -ne [Globalization.UnicodeCategory]::NonSpacingMark) {
            $char
        }
    }
    return (-join $chars) -replace '[^A-Z0-9]+', ' '
}

function Parse-Decimal([string]$value) {
    if ([string]::IsNullOrWhiteSpace($value)) { return $null }
    $normalized = $value.Trim() -replace '\s', '' -replace ',', '.'
    $number = 0.0
    if ([double]::TryParse($normalized, [Globalization.NumberStyles]::Float, [Globalization.CultureInfo]::InvariantCulture, [ref]$number)) {
        return [math]::Round($number, 3)
    }
    return $null
}

function Get-CategoryMapping([string]$sourceType) {
    $key = Normalize-Key $sourceType
    $category = 'Autres'
    $subcategory = ''
    $notes = 'A confirmer avant import.'

    switch -Regex ($key) {
        '^PARE BRISE$' { $category = 'Pare-brise'; $notes = 'Type normalise; aucune sous-categorie Odoo.'; break }
        '^LUNETTES?$' { $category = 'Lunette'; $notes = 'Type normalise; aucune sous-categorie Odoo.'; break }
        '^GLACES LATERALES?$' { $category = 'Glace laterale'; $notes = 'Inclut glaces laterales, custodes et deflecteurs.'; break }
        '^(JOINTS?|ENJOLIVEURS?)$' { $category = 'Joint'; $notes = 'Inclut joints et enjoliveurs.'; break }
        '^(TOIT|TOIT PANO|VITRE PAVILLON)' { $notes = 'Normaliser le libelle article en Toit panoramique; categorie Odoo Autres; aucune sous-categorie.'; break }
        '^(OPTIQUE|OPTIQUES|FEU|PHARE|PHARES|FAISCEAU|ANTIBROUILLARD)' { $notes = 'Regrouper les libelles dans la categorie Odoo Autres; aucune sous-categorie Optique/Phare.'; break }
        '^RETROVISEUR INT$' { $notes = 'Conserver le libelle article Retroviseur INT; categorie Odoo Autres; aucune sous-categorie.'; break }
        '^RETROVISEUR$' { $notes = 'Renommer le libelle article en Retroviseur EXT; categorie Odoo Autres; aucune sous-categorie.'; break }
        '^CACHE RETRO' { $notes = 'Regrouper les libelles sous Cache retro; categorie Odoo Autres; aucune sous-categorie.'; break }
        '^(LEVE VITRE|MECANISME LV|MECANISME)' { $notes = 'Regrouper les libelles sous Leve-vitre; categorie Odoo Autres; aucune sous-categorie.'; break }
        '^BAIE DE PARE BRISE$' { $notes = 'Categorie Odoo Autres; aucune sous-categorie.'; break }
        '^CAMERA$' { $notes = 'Article rare : categorie Odoo Autres, aucune categorie Camera.'; break }
        '^AUTRES$' { $notes = 'Categorie Odoo Autres; valeur fourre-tout controlee.'; break }
        '^$' { $notes = 'TYPE absent : classification manuelle requise.'; break }
        default { $notes = 'Valeur source rare ou non documentee : categorie Odoo Autres, classification manuelle requise.'; break }
    }

    [PSCustomObject]@{
        source_type = if ([string]::IsNullOrWhiteSpace($sourceType)) { '__VIDE__' } else { $sourceType.Trim() }
        target_category = $category
        target_subcategory = $subcategory
        product_type = 'product'
        stockable = 'true'
        notes = $notes
    }
}

$articleRows = @($rows | Where-Object {
    -not [string]::IsNullOrWhiteSpace($_.eurocode) -and $_.eurocode.Trim() -ne '0'
})
$uniqueCodeCount = @($articleRows | Group-Object { $_.eurocode.Trim() }).Count
$invalidCodeRows = @($articleRows | Where-Object { $_.eurocode.Trim() -in @('-', '---', '?') })
$catalogRows = @($articleRows | Where-Object { $_.eurocode.Trim() -notin @('-', '---', '?') })

$categoryMappings = @($articleRows | Group-Object { if ([string]::IsNullOrWhiteSpace($_.source_type)) { '__VIDE__' } else { $_.source_type.Trim() } } | ForEach-Object {
    Get-CategoryMapping $_.Name
}) | Sort-Object source_type
$categoryMappings | Export-Csv -Path (Join-Path $folder 'categories_mapping.csv') -Delimiter ';' -NoTypeInformation -Encoding UTF8

$locationMappings = @($articleRows | Where-Object { -not [string]::IsNullOrWhiteSpace($_.place) } | Group-Object { $_.place.Trim() } | ForEach-Object {
    $source = $_.Name
    $key = Normalize-Key $source
    $warehouse = ''
    $parent = ''
    $target = ''
    $status = 'to_check'
    $notes = "Source observee sur $($_.Count) ligne(s)."

    if ($key -eq 'D2') {
        $warehouse = 'RPBM'
        $parent = 'RPBM/Stock D2'
        $target = 'RPBM/Stock D2'
        $status = 'existing_root'
        $notes += ' Racine Odoo existante en preproduction.'
    } elseif ($key -eq 'CASSE') {
        $target = 'Virtual Locations/RPBM: Scrap'
        $status = 'proposed'
        $notes += ' Ne doit pas alimenter le stock vendable.'
    } elseif ($key -match '^(CENTRE|GALLERIA|GENIPA)$') {
        $notes += ' Zone connue mais rattachement D1/D2 a confirmer.'
    } elseif ($key -match '^(R|J|T)[0-9A-Z]+$') {
        $notes += ' Rack/zone : depot D1 ou D2 a confirmer.'
    } else {
        $notes += ' Valeur heterogene : rattachement a confirmer.'
    }

    [PSCustomObject]@{
        source_place = $source
        warehouse = $warehouse
        location_parent = $parent
        location_name = if ($target) { ($target -split '/')[-1] } else { '' }
        location_complete_name = $target
        mapping_status = $status
        source_row_count = $_.Count
        notes = $notes
    }
}) | Sort-Object source_place
$locationMappings | Export-Csv -Path (Join-Path $folder 'locations_mapping.csv') -Delimiter ';' -NoTypeInformation -Encoding UTF8

$productRows = @($catalogRows | Group-Object { $_.eurocode.Trim() } | ForEach-Object {
    $group = $_.Group
    $first = $group | Select-Object -First 1
    $mapping = Get-CategoryMapping $first.source_type
    $names = @($group | Where-Object { -not [string]::IsNullOrWhiteSpace($_.designation) } | ForEach-Object { $_.designation.Trim() } | Select-Object -Unique)
    $purchasePrices = @($group | ForEach-Object { Parse-Decimal $_.purchase_price } | Where-Object { $_ -ne $null -and $_ -gt 0 } | Select-Object -Unique)
    $publicPrices = @($group | ForEach-Object { Parse-Decimal $_.public_price } | Where-Object { $_ -ne $null -and $_ -gt 0 } | Select-Object -Unique)
    [PSCustomObject]@{
        product_reference = $_.Name
        product_name = if ($names.Count) { $names[0] } else { $_.Name }
        source_type = if ($first.source_type) { $first.source_type.Trim() } else { '__VIDE__' }
        target_category = $mapping.target_category
        target_subcategory = $mapping.target_subcategory
        product_type = $mapping.product_type
        stockable = $mapping.stockable
        purchase_price = if ($purchasePrices.Count) { $purchasePrices[0] } else { '' }
        public_price = if ($publicPrices.Count) { $publicPrices[0] } else { '' }
        source_row_count = $group.Count
        source_places = (@($group | Where-Object { $_.place } | ForEach-Object { $_.place.Trim() } | Select-Object -Unique) -join ' | ')
        import_status = 'to_check'
        notes = if ($group.Count -gt 1) { 'Doublon source consolide : controler quantites, prix et emplacements.' } else { 'Rapprochement Odoo par default_code a effectuer.' }
    }
}) | Sort-Object product_reference
$productRows | Export-Csv -Path (Join-Path $folder 'products_to_import.csv') -Delimiter ';' -NoTypeInformation -Encoding UTF8

@('product_reference;product_name;category;location;quantity;cost;public_price;status;inventory_status;notes') | Set-Content -Path (Join-Path $folder 'stock_initial_to_import.csv') -Encoding UTF8

$positiveRows = @($articleRows | Where-Object { (Parse-Decimal $_.quantity_current) -gt 0 })
$duplicateGroups = @($articleRows | Group-Object { $_.eurocode.Trim() } | Where-Object Count -gt 1)
$rowsWithoutExit = @($articleRows | Where-Object { [string]::IsNullOrWhiteSpace($_.date_exit) })
$reconciliationSection = ''
$reconciliationPath = Join-Path $folder 'product_reconciliation.csv'
if (Test-Path $reconciliationPath) {
    $reconciliationRows = @(Import-Csv -Delimiter ';' $reconciliationPath)
    $createCandidates = @($reconciliationRows | Where-Object decision -eq 'create_candidate').Count
    $existingReviews = @($reconciliationRows | Where-Object decision -eq 'existing_review').Count
    $odooOnly = @($reconciliationRows | Where-Object decision -eq 'odoo_only').Count
    $reconciliationSection = @"
## Rapprochement catalogue Odoo

Lecture du catalogue Odoo realisee via Paradigme MCP et comparaison par default_code :

- $createCandidates candidats source absents du catalogue Odoo;
- $existingReviews references source deja presentes dans Odoo;
- $odooOnly produits Odoo avec reference absents du CSV candidat.

Conclusion : aucune creation ne doit etre lancee sans validation du contenu des candidats et des 58 produits Odoo sans reference interne exploitable.

"@
}
$qualityReport = @"
# Rapport de qualite des donnees de migration

Date de generation : $(Get-Date -Format 'yyyy-MM-dd')
Source : `Gestion Stock V4 - Stock Complet.csv` (export du 29/01/2025)
Statut : preparation uniquement, aucune ecriture Odoo.

## Source CSV

| Controle | Resultat |
|---|---:|
| Lignes articles avec EUROCODE | $($articleRows.Count) |
| EUROCODE uniques | $uniqueCodeCount |
| References invalides (`-`, `---`, `?`) | $($invalidCodeRows.Count) |
| EUROCODE apparaissant plusieurs fois | $($duplicateGroups.Count) |
| Lignes avec quantite actuelle positive | $($positiveRows.Count) |
| Quantite positive totale | $([math]::Round((@($positiveRows | ForEach-Object { Parse-Decimal $_.quantity_current } | Measure-Object -Sum).Sum), 3)) |
| Lignes sans DATE SORTIE | $($rowsWithoutExit.Count) |
| Emplacements source distincts | $($locationMappings.Count) |
| Types source distincts | $($categoryMappings.Count) |

## Odoo preproduction lu via Paradigme MCP

- 13 categories produits existantes.
- 169 produits existants : 58 stockables, 75 consommables, 36 services.
- 1 entrepot actif : `RPBM`.
- 438 emplacements internes, dont 434 sous `RPBM/Stock D1` et `RPBM/Stock D2`.
- Les categories existantes utilisent des politiques mixtes : ``average``/``real_time`` pour certaines familles et ``standard``/``manual_periodic`` pour d'autres.

${reconciliationSection}## Anomalies et risques

- Le CSV contient $uniqueCodeCount references distinctes contre 168 produits Odoo : le rapprochement par ``default_code`` est obligatoire avant toute creation.
- Les $($invalidCodeRows.Count) lignes portant une reference manifestement invalide sont exclues de `products_to_import.csv` et restent a investiguer.
- Les doublons EUROCODE doivent etre agregees par article, quantite et emplacement; ils ne doivent pas creer plusieurs fiches produit.
- Le CSV est anterieur a l'inventaire du 30/06/2026. Il ne constitue pas une source fiable pour le stock initial final.
- Les couleurs Google Sheets ne sont pas conservees dans le CSV; les statuts vendu/reserve/casse doivent etre confirmes par une colonne ou une source complementaire.
- Le rattachement de nombreux ``PLACE`` a D1 ou D2 reste a confirmer. Les lignes correspondantes sont marquees ``to_check`` dans `locations_mapping.csv`.

## Fichiers produits

- `categories_mapping.csv` : mapping des types sources vers les categories cibles.
- `locations_mapping.csv` : mapping des emplacements source et anomalies de rattachement.
- `products_to_import.csv` : catalogue dedoublonne par EUROCODE, encore a rapprocher avec Odoo.
- `stock_initial_to_import.csv` : modele vide volontairement, a remplir depuis l'inventaire valide du 30/06/2026.

## Decisions bloquantes

1. Confirmer les categories et la typologie stockable/consommable/service.
2. Confirmer le rattachement physique D1/D2 des lieux source.
3. Fournir le fichier corrige de l'inventaire du 30/06/2026.
4. Arbitrer l'ecart d'inventaire de 6 448,18 EUR.
5. Valider la methode de cout et la valorisation comptable avant l'ajustement initial.

## Prochaine validation technique

Comparer ``products_to_import.csv`` aux ``default_code`` existants dans Odoo, produire les lignes ``create``, ``update`` et ``to_check``, puis tester l'import du catalogue en preproduction avec confirmation explicite.
"@
$qualityReport | Set-Content -Path (Join-Path $folder 'data_quality_report.md') -Encoding UTF8

Write-Output "Generated: categories_mapping.csv, locations_mapping.csv, products_to_import.csv, stock_initial_to_import.csv, data_quality_report.md"
