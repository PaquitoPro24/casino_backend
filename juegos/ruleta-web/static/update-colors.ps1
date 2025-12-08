# Script to update colors in style.css
$cssFile = "style.css"
$content = Get-Content $cssFile -Raw

# Replace colors
$content = $content -replace '#016D29', '#202020'
$content = $content -replace '#F3c620', '#ab925c'
$content = $content -replace '#f3c620', '#ab925c'
$content = $content -replace '#d3b201', '#ab925c'
$content = $content -replace '#d5b714', '#ab925c'
$content = $content -replace '#ffec00', '#ab925c'

# Update specific elements
$content = $content -replace '(#notification\s*\{[^}]*background-color:\s*)#ad0205', '$1#202020'
$content = $content -replace '(\.nBtn\s*\{[^}]*background-color:\s*)green', '$1#ab925c'
$content = $content -replace '(\.nBtn\s*\{[^}]*)(border-radius)', '$1color: #202020; font-weight: bold; $2'
$content = $content -replace '(\.spinBtn\s*\{[^}]*)(color:\s*)#000', '$1$2#202020'
$content = $content -replace '(\.bank,\s*\.bet\s*\{[^}]*border:\s*4px solid\s*)silver', '$1#ab925c'
$content = $content -replace '(\.bank,\s*\.bet\s*\{[^}]*)(text-align)', '$1color: #ab925c; $2'
$content = $content -replace '(#pnContent\s*\{[^}]*background-color:\s*)#fff', '$1#202020'
$content = $content -replace '(#pnContent\s*\{[^}]*)(color:\s*)#000', '$1$2#ab925c'

# Add background pattern to body
$content = $content -replace '(body\s*\{[^}]*)(user-select:\s*none;)', '$1$2`r`n`tbackground-color: #202020;`r`n`tbackground-image: url(''/static/pattern-bg.jpg'');`r`n`tbackground-repeat: repeat;`r`n`tbackground-size: 400px 400px;'

# Update container background
$content = $content -replace '(#container\s*\{[^}]*background-color:\s*)#016D29', '$1transparent'
$content = $content -replace '(#container\s*\{[^}]*)(color:\s*)#fff', '$1$2#ab925c'

# Add semi-transparent backgrounds to betting elements
$content = $content -replace '(\.bbtoptwo\s*\{[^}]*)(font-weight:\s*bold;)', '$1$2`r`n`tbackground-color: rgba(32, 32, 32, 0.7);'
$content = $content -replace '(\.number_block\s*\{[^}]*)(padding:\s*32px 0px;)', '$1$2`r`n`tbackground-color: rgba(32, 32, 32, 0.7);'
$content = $content -replace '(\.bo3_block,\s*\.oto_block\s*\{[^}]*)(font-size:\s*20px;)', '$1$2`r`n`tbackground-color: rgba(32, 32, 32, 0.7);'
$content = $content -replace '(\.number_0\s*\{[^}]*)(border-top-left-radius:\s*100%;)', '$1$2`r`n`tbackground-color: rgba(32, 32, 32, 0.7);'
$content = $content -replace '(\.tt1_block\s*\{[^}]*)(margin-top:\s*-89\.75px;)', '$1$2`r`n`tbackground-color: rgba(32, 32, 32, 0.7);'
$content = $content -replace '(\.chipDeck,\s*\.bankContainer\s*\{[^}]*)(box-shadow:[^;]+;)', '$1$2`r`n`tbackground-color: rgba(32, 32, 32, 0.8);'
$content = $content -replace '(\.pnBlock\s*\{[^}]*)(margin-left:\s*-1px;)', '$1$2`r`n`tbackground-color: rgba(32, 32, 32, 0.8);'

# Update mobile background
$content = $content -replace '(only screen and \(max-height: 550px\) \{[^}]*background-color:\s*)#016D29', '$1#202020'
$content = $content -replace '(only screen and \(max-height: 550px\) \{[^}]*)(background-color:\s*#202020;)', '$1$2`r`n`t`tbackground-image: url(''/static/pattern-bg.jpg'');`r`n`t`tbackground-repeat: repeat;`r`n`t`tbackground-size: 400px 400px;'

Set-Content $cssFile -Value $content -NoNewline
Write-Host "Colors updated successfully!"
