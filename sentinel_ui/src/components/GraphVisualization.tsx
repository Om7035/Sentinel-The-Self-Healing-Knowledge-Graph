"use client";

import dynamic from 'next/dynamic';
import { useMemo } from 'react';
import * as THREE from 'three';

// Dynamically import ForceGraph3D with no SSR
const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), {
    ssr: false,
    loading: () => <div className="flex items-center justify-center h-full text-white">Loading Graph...</div>
});

interface GraphData {
    nodes: Array<{ id: string; label: string;[key: string]: any }>;
    links: Array<{ source: string; target: string; relation: string;[key: string]: any }>;
}

interface GraphVisualizationProps {
    data: GraphData;
}

export default function GraphVisualization({ data }: GraphVisualizationProps) {
    // Memoize graph config to prevent unnecessary re-renders
    const graphConfig = useMemo(() => ({
        nodeLabel: "id",
        nodeAutoColorBy: "label",
        linkDirectionalArrowLength: 3.5,
        linkDirectionalArrowRelPos: 1,
        linkLabel: "relation",
        linkWidth: 1.5,
        linkOpacity: 0.7,
        nodeThreeObject: (node: { id?: string | number; x?: number; y?: number; z?: number; vx?: number; vy?: number; vz?: number; fx?: number; fy?: number; fz?: number; color?: string }) => {
            const sphere = new THREE.Mesh(
                new THREE.SphereGeometry(5),
                new THREE.MeshBasicMaterial({
                    color: node.color || '#00ff00',
                    transparent: true,
                    opacity: 0.9
                })
            );
            sphere.add(new THREE.PointLight(node.color || '#00ff00', 1, 15));
            return sphere;
        },
        linkCurvature: 0.25,
        linkDirectionalParticles: 4,
        linkDirectionalParticleSpeed: 0.005,
    }), []);

    return (
        <div className="w-full h-full bg-slate-900 rounded-lg overflow-hidden border border-slate-700 shadow-xl">
            <ForceGraph3D
                graphData={data}
                {...graphConfig}
                backgroundColor="#0f172a" // slate-900
                nodeRelSize={6}
            />
        </div>
    );
}
