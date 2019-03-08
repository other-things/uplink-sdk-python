global int x = 0 ;

transition initial -> set;
transition set -> terminal;

@set
end () {
  terminate();
}

@initial
setX (int z) {
  x = 42 + y;
  transitionTo(@set);
}
