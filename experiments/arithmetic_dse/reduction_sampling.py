"""Canonical fused-region sampling RTL and independent integer reference.

G's production emitter uses the same fixed-width zero-padded sum lowering.
The wrapper matches the existing operator label reader's service/capture banks.
"""
from .reduction_function import features


def geometry(query):
    width, terms = query['output_bits'], query['terms']
    features(width, terms, 1500.)
    # Independent packed launch bits; source IDs never enter numerical features.
    offsets = {}; n = 0
    for term in terms:
        for source, bit, _ in term:
            offsets[source, bit] = n; n += 1
    tokens = [('producer', b) for b in range(width)]
    return dict(input_bits=n, output_bits=width, offsets=offsets,
                captures=[dict(id='direct0bank0', tokens=tokens, live_tokens=tokens)])


def evaluate(query, word):
    g = geometry(query)
    return sum(sum(((word >> g['offsets'][s, b]) & 1) << c for s, b, c in term)
               for term in query['terms']) & ((1 << query['output_bits']) - 1)


def source(query, name='ModelBundle'):
    g = geometry(query); n, w = g['input_bits'], g['output_bits']; sums = []
    for i, term in enumerate(query['terms']):
        columns = {c: g['offsets'][s, b] for s, b, c in term}
        vector = ','.join('a['+str(columns[c])+']' if c in columns else "1'b0" for c in reversed(range(w)))
        sums.append(f'wire [{w-1}:0] t{i}={{{vector}}};')
    return f'''(* keep_hierarchy=1 *) module {name}Reduce(input wire [{n-1}:0] a,output wire [{w-1}:0] value);
{''.join(sums)}
assign value={'+'.join('t'+str(i) for i in range(len(sums)))};
endmodule
(* keep_hierarchy=1 *) module {name}Launch(input wire clk,rstn,iv,input wire [{n-1}:0] data,output reg [{n-1}:0] value,output reg valid);
(* keep *) always @(posedge clk)if(!rstn)begin value<=0;valid<=0;end else begin valid<=iv;if(iv)value<=data;end
endmodule
(* keep_hierarchy=1 *) module {name}Capture(input wire clk,rstn,iv,input wire [{w-1}:0] value,output wire [{w-1}:0] data,output reg valid);
(* keep,dont_touch *) reg [{w-1}:0] storage0;
(* keep *) always @(posedge clk)storage0<=value;
(* keep *) always @(posedge clk)if(!rstn)valid<=0;else valid<=iv;
assign data=storage0;
endmodule
(* keep_hierarchy=1 *) module {name}Observer(input wire [{w-1}:0] data,output wire [0:0] y);assign y[0]=^data;endmodule
module {name}(input wire clk,rstn,iv,input wire [{n-1}:0] data,output wire [0:0] y,output wire ov);
wire [{n-1}:0] launched;wire launch_valid;wire [{w-1}:0] observed,producer_value;
{name}Launch launch(.clk(clk),.rstn(rstn),.iv(iv),.data(data),.value(launched),.valid(launch_valid));
{name}Reduce core(.a(launched),.value(producer_value));
{name}Capture capture(.clk(clk),.rstn(rstn),.iv(launch_valid),.value(producer_value),.data(observed),.valid(ov));
{name}Observer observer(.data(observed),.y(y));
endmodule
'''


def geometry_contract(query):
    g = geometry(query)
    return dict(launch_FF_bits=g['input_bits']+1, capture_FF_bits=g['output_bits']+1)
