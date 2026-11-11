# Qwen3-30B-A3B-W8A8 TP4 Profiling

2026 年 11 月 10 日采集。归档包含本地同步目录的全部 53 个文件，包括四个 rank 的时间线、算子与通信统计、SQLite 数据库、前端 trace 和采集时间记录。公开版将 A2 主机名替换为别名。

归档共 156,692,920 字节。请下载以下 2 个分卷到同一目录。

- [numa24_visible8_tp4_profile_20261110.tar.xz.part01](numa24_visible8_tp4_profile_20261110.tar.xz.part01)（99,614,720 字节）
- [numa24_visible8_tp4_profile_20261110.tar.xz.part02](numa24_visible8_tp4_profile_20261110.tar.xz.part02)（57,078,200 字节）

在该目录运行 PowerShell，按文件名顺序合并分卷，校验 SHA-256 后解压。

~~~powershell
$archive = Join-Path (Get-Location).ProviderPath 'numa24_visible8_tp4_profile_20261110.tar.xz'
$parts = @(Get-ChildItem -File -Filter 'numa24_visible8_tp4_profile_20261110.tar.xz.part*' | Sort-Object Name)
if ($parts.Count -ne 2) { throw '分卷数量不符' }
$out = [IO.File]::Open($archive, [IO.FileMode]::CreateNew)
try {
    foreach ($part in $parts) {
        $in = [IO.File]::OpenRead($part.FullName)
        try { $in.CopyTo($out) } finally { $in.Dispose() }
    }
} finally { $out.Dispose() }
if ((Get-FileHash $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'afbcb12bed3d71dd4586b71e407df287390cbaecfab7548949afbe8b2f69e874') {
    throw '合并后的 SHA-256 不符'
}
tar -xf $archive
~~~
