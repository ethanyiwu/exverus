use vstd::prelude::*;

verus! {

fn encode_char(c: u8) -> (r: u8)
    requires
        65 <= c <= 90,
    ensures
        r == encode_char_spec(c as int),
        65 <= r <= 90,
{
    (c - 65 + 5) % 26 + 65
}

fn decode_char(c: u8) -> (r: u8)
    requires
        65 <= c <= 90,
    ensures
        r == decode_char_spec(c as int),
        65 <= r <= 90,
{
    (c - 65 + 26 - 5) % 26 + 65
}

#[verifier::loop_isolation(false)]
fn encode_shift(s: &Vec<u8>) -> (t: Vec<u8>)
    requires
        forall|i: int| #![trigger s[i]] 0 <= i < s.len() ==> 65 <= s[i] <= 90,
    ensures
        s.len() == t.len(),
        forall|i: int| #![auto] 0 <= i < t.len() ==> t[i] == encode_char_spec(s[i] as int),
        forall|i: int| #![auto] 0 <= i < t.len() ==> decode_char_spec(t[i] as int) == s[i],
{
    let mut t: Vec<u8> = vec![];
    for i in 0..s.len()
    {
        t.push(encode_char(s[i]));
    }
    t
}

#[verifier::loop_isolation(false)]
fn decode_shift(s: &Vec<u8>) -> (t: Vec<u8>)
    requires
        forall|i: int| #![trigger s[i]] 0 <= i < s.len() ==> 65 <= s[i] <= 90,
    ensures
        s.len() == t.len(),
        forall|i: int| #![auto] 0 <= i < t.len() ==> t[i] == decode_char_spec(s[i] as int),
        forall|i: int| #![auto] 0 <= i < t.len() ==> encode_char_spec(t[i] as int) == s[i],
{
    let mut t: Vec<u8> = vec![];
    for i in 0..s.len()
    {
        t.push(decode_char(s[i]));
    }
    t
}

}
fn main() {}
