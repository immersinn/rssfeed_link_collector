#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  1 11:44:43 2017

@author: immersinn
"""


import igraph
import plotly.graph_objs as pogo



def create_igraph(vertices, edges, 
                  vert_attrs = ['name'],
                  edge_attrs = ['weight']):
    
    G = igraph.Graph()
    
    G.add_vertices(len(vertices))
    for va in vert_attrs:
        G.vs[va] = [v[va] for v in vertices]
        
    for e in edges:
        G.add_edge(str(e['from']), 
                   str(e['to']))
    for ea in edge_attrs:
        G.es[ea] = [e[ea] for e in edges]
        
    return(G)


def create_graph_fig_simple(GG,
                            title="", plot_subtext="",
                            show_colorscale_legend=False, colorscale='Jet'):
    
    # Create layout
    V = list(GG.vs)
    labels = list(GG.vs['name'])
    N = len(labels)
    E = [e.tuple for e in GG.es] # list of edges
    layt = GG.layout('kk') # kamada-kawai layout
    
    # Nodes
    Xn=[layt[k][0] for k in range(N)]
    Yn=[layt[k][1] for k in range(N)]

    node_trace = pogo.Scatter(
        x=Xn,
        y=Yn, 
        text=[],
        mode='markers', 
        hoverinfo='text',
        showlegend=True,
        marker=pogo.Marker(
            showscale=show_colorscale_legend,
            colorscale=colorscale,
            reversescale=True,
            color=[], 
            size=10,         
            colorbar=dict(
                thickness=15,
                title=title,
                xanchor='left',
                titleside='right'
            ),
            line=dict(width=2)))
    
    # Edges
    Xe=[]
    Ye=[]
    for e in E:
        Xe+=[layt[e[0]][0],layt[e[1]][0], None]
        Ye+=[layt[e[0]][1],layt[e[1]][1], None]
        
    edge_trace = pogo.Scatter(x=Xe,
               y=Ye,
               mode='lines',
               line=pogo.Line(color='rgb(210,210,210)', width=1),
               hoverinfo='none'
               )
        
        
    fig = pogo.Figure(data=pogo.Data([edge_trace, node_trace]),
             layout=pogo.Layout(
                title=title,
                titlefont=dict(size=16),
                showlegend=False, 
                width=650,
                height=650,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                annotations=[ dict(
                    text=plot_subtext,
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002 ) ],
                xaxis=pogo.XAxis(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=pogo.YAxis(showgrid=False, zeroline=False, showticklabels=False)))
    
    return(fig)


def create_graph_fig(GG,
                     show_groups=True, weighted_edges=True,
                     title="", plot_subtext="",
                     show_colorscale_legend=False, colorscale='Jet'):
    
    # Create layout
    V = list(GG.vs)
    labels = list(GG.vs['name'])
    N = len(labels)
    E = [e.tuple for e in GG.es] # list of edges
    layt = GG.layout('kk') # kamada-kawai layout
    
    # Nodes
    Xn=[layt[k][0] for k in range(N)]
    Yn=[layt[k][1] for k in range(N)]

    node_trace = pogo.Scatter(
        x=Xn,
        y=Yn, 
        text=[],
        mode='markers', 
        hoverinfo='text',
        showlegend=True,
        marker=pogo.Marker(
            showscale=show_colorscale_legend,
            colorscale=colorscale,
            reversescale=True,
            color=[], 
            size=10,         
            colorbar=dict(
                thickness=15,
                title=title,
                xanchor='left',
                titleside='right'
            ),
            line=dict(width=2)))
    
    if show_groups:
        for i,v in enumerate(GG.vs()):
            node_trace['marker']['color'].append(v['group'])
            node_info = v['label'][:20] + ' (' + str(v['group']) + ')'
            node_trace['text'].append(node_info)
    
    
    # Edges
    if weighted_edges:
        
        lines=[] # the list of dicts defining   edge  Plotly attributes
        edge_info=[] # the list of points on edges where  the information is placed

        for j, e in enumerate(E):
            xs = [layt[e[0]][0],layt[e[1]][0]]
            ys = [layt[e[0]][1],layt[e[1]][1]]
            w = GG.es[j]['weight']

            lines.append(pogo.Scatter(x=xs,
                                 y=ys,
                                 mode='lines',
                                 line=pogo.Line(color='#888',
                                          width=w / 2 # The  width is proportional to the edge weight
                                         ),
                                hoverinfo='none'
                               )
                        )
            
        edge_trace = lines + edge_info

    else:
        
        Xe=[]
        Ye=[]
        for e in E:
            Xe+=[layt[e[0]][0],layt[e[1]][0], None]
            Ye+=[layt[e[0]][1],layt[e[1]][1], None]

        edge_trace = pogo.Scatter(x=Xe,
                   y=Ye,
                   mode='lines',
                   line=pogo.Line(color='rgb(210,210,210)', width=1),
                   hoverinfo='none'
                   )
        edge_trace = [edge_trace]
        
        
    fig = pogo.Figure(data=pogo.Data(edge_trace + [node_trace]),
             layout=pogo.Layout(
                title=title,
                titlefont=dict(size=16),
                showlegend=False, 
                width=650,
                height=650,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                annotations=[ dict(
                    text=plot_subtext,
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002 ) ],
                xaxis=pogo.XAxis(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=pogo.YAxis(showgrid=False, zeroline=False, showticklabels=False)))
    
    return(fig)


