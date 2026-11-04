import pathlib
root=pathlib.Path(__file__).resolve().parent
source=(root.parent/'reproduction/kit/inside_runner.py').read_text(encoding='utf8')
source=source.replace('0be0a6156ce331d4b2a4249d671dfc2876f71908','b3b82c137ee242a774c29b56325133771f5f069d')
source=source.replace("'torch-npu': '2.10.0.post7'","'torch-npu': '2.10.0.post4'")
source=source.replace("'triton-ascend': '3.6.0'","'triton-ascend': '3.2.2'")
source=source.replace('V100R001C12SPC002B200','V100R001C12SPC002B201')
source=source.replace('run the pinned CI pytest','run the pinned CI pytest')
source=source.replace('41119764915/job/124286288200','41327490550/job/124914290773')
source=source.replace('124286288200','124914290773').replace('757.2505','767.3497').replace('757_2505','767_3497')
(root/'inside_runner.py').write_text(source,encoding='utf8')
print('Prepared new-target runner; validate package versions against pulled image before executing.')
