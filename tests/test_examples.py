import pytest
from lektor.project import Project


skipif_not_36 = pytest.mark.skipif("sys.version_info < (3, 6)")


def discover_pages(root=None):
    if not root:
        pad = Project.discover().make_env().new_pad()
        return discover_pages(pad.root)
    ret = [root]
    for page in root.children:
        ret.extend(discover_pages(page))
    return ret


def pytest_generate_tests(metafunc):
    if metafunc.function.__name__ == 'test_example':
        args = []
        for page in discover_pages():
            if page['_model'] != 'example':
                continue
            for i, example_block in enumerate(page['examples'].blocks):
                blocks = {
                    example.flowblockmodel.id.replace('code_block_', ''): example['code'].source
                    for example in example_block['examples'].blocks
                    if 'code_block_' in example.flowblockmodel.id
                }
                skipif = pytest.mark.skipif(
                    "sys.version_info < ({}, {})".format(
                        *example_block['availability'].strip('py')))
                setup = blocks.get('setup', "")
                result = next(
                    b for b
                    in example_block['examples'].blocks
                    if 'result' in b
                )['result']
                for block_type in ['mod', 'format', 'fstr']:
                    if block_type in blocks:
                        if block_type == 'fstr':
                            skipif = skipif_not_36
                        args.append(
                            skipif(
                                (
                                    "{}_{}".format(page['_id'], i),
                                    block_type,
                                    "\n".join([setup, "out = {}".format(blocks[block_type])]),
                                    result
                                )
                            )
                        )
        return metafunc.parametrize(
            ('name', 'type', 'code', 'output'),
            args
        )


def test_example(name, type, code, output):
    ctx = {}
    exec(code, ctx)
    assert ctx['out'] == output
