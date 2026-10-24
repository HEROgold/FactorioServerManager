"""Mod dependency parsing and graph helpers, as properties over generated mods."""

from hypothesis import given  # skylos: ignore[SKY-D223] -- dev dependency
from hypothesis import strategies as st  # skylos: ignore[SKY-D223] -- dev dependency

from api._types.mod_deps import (
    closure,
    parse_dependency,
    required_dependency_names,
    reverse_graph,
)
from tests.strategies import mod_names

KINDS = {
    "": "required",
    "~ ": "required",
    "? ": "optional",
    "(?) ": "optional",
    "! ": "incompatible",
}
versions = st.from_regex(r"[0-9]{1,2}(\.[0-9]{1,2}){0,2}", fullmatch=True)
constraints = st.one_of(
    st.just(""),
    st.tuples(st.sampled_from([">=", ">", "=", "<", "<="]), versions).map(
        lambda c: f" {c[0]} {c[1]}",
    ),
)
graphs = st.dictionaries(mod_names, st.sets(mod_names, max_size=4), max_size=8)


@given(prefix=st.sampled_from(sorted(KINDS)), name=mod_names, constraint=constraints)
def test_parse_dependency_reads_kind_and_name(
    prefix: str,
    name: str,
    constraint: str,
) -> None:
    assert parse_dependency(f"{prefix}{name}{constraint}") == (KINDS[prefix], name)


@given(names=st.lists(mod_names, max_size=6))
def test_required_names_skip_base_core_and_non_required(names: list[str]) -> None:
    dependencies = [
        "base >= 2.0",
        "core",
        *names,
        *(f"? opt-{n}" for n in names),
        *(f"! bad-{n}" for n in names),
    ]

    assert required_dependency_names(dependencies) == set(names) - {"base", "core"}


@given(graph=graphs, start=mod_names)
def test_closure_holds_start_and_everything_it_reaches(
    graph: dict[str, set[str]],
    start: str,
) -> None:
    reached = closure(start, graph)

    assert start in reached
    for name in reached:
        assert graph.get(name, set()) <= reached


@given(graph=graphs)
def test_reverse_graph_flips_every_edge(graph: dict[str, set[str]]) -> None:
    reversed_graph = reverse_graph(graph)

    edges = {(mod, dep) for mod, deps in graph.items() for dep in deps}
    flipped = {(mod, dep) for dep, mods in reversed_graph.items() for mod in mods}
    assert flipped == edges
    assert set(graph) <= set(reversed_graph)
