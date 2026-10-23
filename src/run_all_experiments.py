from __future__ import annotations
from pathlib import Path
import json, hashlib, math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from oft_invariants import (
    SEED, random_orthogonal, bessel_zeros, exact_odd_roots,
    fd_sturm_liouville_roots, spectral_discriminant,
    reconstructibility_stats,
)

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
FIG = ROOT / "figures"
RES.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
rng = np.random.default_rng(SEED)

# ---------- Round I: representation invariance ----------
rows = []
# E1 spectral conjugation
errs_eig=[]; raw=[]; trerr=[]
for _ in range(1000):
    A=rng.normal(size=(8,8)); O=A.T@A+0.25*np.eye(8); U=random_orthogonal(rng,8); Op=U@O@U.T
    e=np.linalg.eigvalsh(O); ep=np.linalg.eigvalsh(Op)
    errs_eig.append(np.linalg.norm(ep-e)/np.linalg.norm(e))
    raw.append(np.linalg.norm(Op-O,'fro')/np.linalg.norm(O,'fro'))
    p=np.array([np.trace(np.linalg.matrix_power(O,k)) for k in range(1,9)])
    pp=np.array([np.trace(np.linalg.matrix_power(Op,k)) for k in range(1,9)])
    trerr.append(np.linalg.norm(pp-p)/np.linalg.norm(p))
rows += [
    ["E1","spectral conjugation","median eigenvalue relative error",np.median(errs_eig),1000],
    ["E1","spectral conjugation","median raw matrix relative change",np.median(raw),1000],
    ["E1","spectral conjugation","median power-trace relative error",np.median(trerr),1000],
]

# E2 perturbation sensitivity
pert=[]
baseA=rng.normal(size=(8,8)); baseO=baseA.T@baseA+np.eye(8); basee=np.linalg.eigvalsh(baseO)
for eps in [1e-8,1e-6,1e-4,1e-2,1e-1]:
    vals=[]
    for _ in range(400):
        H=rng.normal(size=(8,8)); H=(H+H.T)/2; H*=np.linalg.norm(baseO,'fro')/np.linalg.norm(H,'fro')
        U=random_orthogonal(rng,8); Op=U@baseO@U.T+eps*H
        vals.append(np.linalg.norm(np.linalg.eigvalsh(Op)-basee)/np.linalg.norm(basee))
    pert.append([eps,np.median(vals),np.quantile(vals,.1),np.quantile(vals,.9)])
pert_df=pd.DataFrame(pert,columns=["epsilon","median_spectral_deviation","q10","q90"])
pert_df.to_csv(RES/"round1_spectral_perturbation.csv",index=False)
fit=np.polyfit(np.log10(pert_df.epsilon),np.log10(pert_df.median_spectral_deviation),1)[0]
rows.append(["E2","non-isospectral control","log-log spectral sensitivity slope",fit,len(pert_df)])

# E3 weighted Gram
correct=[]; wrong=[]
for _ in range(500):
    n=7; p=4
    M=rng.normal(size=(n,n)); W=M.T@M+np.eye(n); F=rng.normal(size=(n,p))
    G=F.T@W@F
    A=rng.normal(size=(n,n)); A+=3*np.eye(n)
    Fi=np.linalg.solve(A,F); Wp=A.T@W@A
    correct.append(np.linalg.norm(Fi.T@Wp@Fi-G,'fro')/np.linalg.norm(G,'fro'))
    wrong.append(np.linalg.norm(Fi.T@W@Fi-G,'fro')/np.linalg.norm(G,'fro'))
rows += [["E3","weighted Gram","median covariant-metric error",np.median(correct),500],
         ["E3","weighted Gram","median fixed-metric negative-control error",np.median(wrong),500]]

# E4 overlap covariance
entry=[]; spe=[]
for _ in range(1000):
    A=rng.normal(size=(6,6)); C=(A+A.T)/2; U=random_orthogonal(rng,6); Cp=U.T@C@U
    entry.append(np.linalg.norm(Cp-C,'fro')/np.linalg.norm(C,'fro'))
    spe.append(np.linalg.norm(np.linalg.eigvalsh(Cp)-np.linalg.eigvalsh(C))/np.linalg.norm(np.linalg.eigvalsh(C)))
rows += [["E4","overlap covariance","median entrywise relative change",np.median(entry),1000],
         ["E4","overlap covariance","median spectrum relative error",np.median(spe),1000]]

# E5 degenerate Higgs block
diagchange=[]; hspec=[]
for _ in range(1000):
    A=rng.normal(size=(3,3)); H=(A+A.T)/2; U=random_orthogonal(rng,3); Hp=U.T@H@U
    denom=max(np.linalg.norm(np.diag(H)),1e-12)
    diagchange.append(np.linalg.norm(np.diag(Hp)-np.diag(H))/denom)
    hspec.append(np.linalg.norm(np.linalg.eigvalsh(Hp)-np.linalg.eigvalsh(H))/max(np.linalg.norm(np.linalg.eigvalsh(H)),1e-12))
rows += [["E5","degenerate Higgs","median diagonal-overlap relative change",np.median(diagchange),1000],
         ["E5","degenerate Higgs","median projected-spectrum error",np.median(hspec),1000]]

# ---------- Round II: quotient geometry ----------
# E6 normalization quotient
ratioerr=[]; projerr=[]; coeffchange=[]
for _ in range(2000):
    a=10**rng.uniform(-3,3)*rng.choice([-1,1]); rho=10**rng.uniform(-2,2); b=a*rho
    s=10**rng.uniform(-8,8)*rng.choice([-1,1]); ap,bp=s*a,s*b
    ratioerr.append(abs(bp/ap-rho)/abs(rho))
    v=np.array([a,b]); vp=np.array([ap,bp]); v=v/np.linalg.norm(v); vp=vp/np.linalg.norm(vp)
    projerr.append(min(np.linalg.norm(v-vp),np.linalg.norm(v+vp)))
    coeffchange.append(np.linalg.norm([ap-a,bp-b])/np.linalg.norm([a,b]))
rows += [["E6","normalization quotient","median ratio error",np.median(ratioerr),2000],
         ["E6","normalization quotient","median projective error",np.median(projerr),2000],
         ["E6","normalization quotient","median raw coefficient change",np.median(coeffchange),2000]]

# E7 unit quotient
kaperr=[]; cerr=[]; rawlog=[]
for _ in range(5000):
    k=10**rng.uniform(-2,3); L=10**rng.uniform(-3,2); M=10**rng.uniform(-3,4); u=10**rng.uniform(-9,9)
    kp,Lp,Mp=u*k,L/u,u*M
    kaperr.append(abs(kp*Lp-k*L)/abs(k*L)); cerr.append(abs(Mp/kp-M/k)/abs(M/k))
    rawlog.append(np.linalg.norm(np.log10([kp,Lp,Mp])-np.log10([k,L,M])))
rows += [["E7","unit quotient","median kL relative error",np.median(kaperr),5000],
         ["E7","unit quotient","median M/k relative error",np.median(cerr),5000],
         ["E7","unit quotient","median raw log-parameter displacement",np.median(rawlog),5000]]

# E8 discriminant critical locus
disc=[]
for mu in [0,1e-6,1e-5,1e-4,1e-3,1e-2,1e-1,0.5]:
    vals=np.array([1+mu,1-mu,3.,4.]); d0=spectral_discriminant(vals); rep=[]
    for _ in range(200):
        U=random_orthogonal(rng,4); O=U@np.diag(vals)@U.T; d=spectral_discriminant(np.linalg.eigvalsh(O))
        rep.append(abs(d-d0)/abs(d0) if d0>1e-20 else abs(d-d0))
    disc.append([mu,d0,np.median(rep),1 if mu==0 else 0])
disc_df=pd.DataFrame(disc,columns=["mu","discriminant","median_representation_error","orthogonal_stabilizer_dimension"])
disc_df.to_csv(RES/"round2_discriminant.csv",index=False)
sm=disc_df[(disc_df.mu>0)&(disc_df.mu<=1e-2)]
disc_slope=np.polyfit(np.log10(sm.mu),np.log10(sm.discriminant),1)[0]
rows.append(["E8","critical locus","near-critical discriminant slope",disc_slope,len(sm)])

# E9 joint relational invariant
C1=np.diag([1.,2.,4.,7.]); C2A=np.diag([3.,5.,8.,11.]); P=np.eye(4)[[1,0,2,3]]; C2B=P@C2A@P.T
mixerr=[]; rawpair=[]
for C2 in [C2A,C2B]:
    t0=np.trace(C1@C2)
    for _ in range(1000):
        U=random_orthogonal(rng,4); A=U@C1@U.T; B=U@C2@U.T
        mixerr.append(abs(np.trace(A@B)-t0)/abs(t0))
        rawpair.append(.5*(np.linalg.norm(A-C1,'fro')/np.linalg.norm(C1,'fro')+np.linalg.norm(B-C2,'fro')/np.linalg.norm(C2,'fro')))
rows += [["E9","joint relational","median mixed-trace error",np.median(mixerr),2000],
         ["E9","joint relational","median raw-pair change",np.median(rawpair),2000]]

# E10 reconstructibility ablation
classes=[(s,p,c,r) for s in [0,1] for p in [0,1] for c in [0,1] for r in [0,1]]
idx={"Spec":0,"Parity":1,"Chiral":2,"Relational":3}
sets=[("Full",["Spec","Parity","Chiral","Relational"]),("-Spec",["Parity","Chiral","Relational"]),("-Parity",["Spec","Chiral","Relational"]),("-Chiral",["Spec","Parity","Relational"]),("-Relational",["Spec","Parity","Chiral"]),("Spec only",["Spec"]),("Structural only",["Parity","Chiral"]),("Relational only",["Relational"]),("None",[])]
abr=[]
for name,kept in sets:
    st=reconstructibility_stats(classes,[idx[k] for k in kept]); abr.append([name,*st])
abr_df=pd.DataFrame(abr,columns=["ablation","distinct_fingerprints","mean_compatible_classes","conditional_entropy_bits","reconstructibility_score","max_exact_identity_accuracy"])
abr_df.to_csv(RES/"round2_reconstructibility_ablation.csv",index=False)
rows += [
    ["E10","reconstructibility ablation","full-fingerprint reconstructibility score",float(abr_df.loc[abr_df.ablation=="Full","reconstructibility_score"].iloc[0]),16],
    ["E10","reconstructibility ablation","spectrum-only reconstructibility score",float(abr_df.loc[abr_df.ablation=="Spec only","reconstructibility_score"].iloc[0]),16],
]

# ---------- Final continuum-equivalent warped spectral experiment ----------
# E11 exact boundary determinant vs finite-difference Sturm-Liouville
c0=0.4; nu0=c0+0.5; kappa0=35.0; n_modes=6
exact=exact_odd_roots(nu0,kappa0,n_modes)
conv=[]
for N in [200,400,800,1600,3200,6400]:
    fd=fd_sturm_liouville_roots(nu0,kappa0,N,n_modes)
    rel=np.abs(fd-exact)/exact
    conv.append([N,*fd,*exact,*rel,float(rel.max()),float(np.median(rel))])
cols=["grid_N"]+[f"fd_x{i}" for i in range(1,n_modes+1)]+[f"exact_x{i}" for i in range(1,n_modes+1)]+[f"relerr_x{i}" for i in range(1,n_modes+1)]+["max_relative_error","median_relative_error"]
conv_df=pd.DataFrame(conv,columns=cols)
conv_df.to_csv(RES/"final_fd_convergence.csv",index=False)
fitrows=conv_df[conv_df.grid_N>=400]
conv_order=-np.polyfit(np.log(fitrows.grid_N),np.log(fitrows.max_relative_error),1)[0]
rows.append(["E11","warped FD validation","observed convergence order",conv_order,len(fitrows)])
rows.append(["E11","warped FD validation","N=6400 max relative error",float(conv_df.iloc[-1].max_relative_error),n_modes])

# E12 finite-kappa vs large-warp Bessel-zero approximation
sweep=[]
for c in [-0.4,0.0,0.4,0.8,1.2]:
    nu=c+0.5
    asym=bessel_zeros(nu,4)
    for kap in [3,5,7,10,20,35]:
        ex=exact_odd_roots(nu,kap,4)
        rel=np.abs(ex-asym)/asym
        sweep.append([c,nu,kap,*ex,*asym,*rel,float(rel.max())])
cols=["c","nu","kappa"]+[f"exact_x{i}" for i in range(1,5)]+[f"bessel_x{i}" for i in range(1,5)]+[f"relerr_x{i}" for i in range(1,5)]+["max_relative_error"]
sweep_df=pd.DataFrame(sweep,columns=cols)
sweep_df.to_csv(RES/"final_bessel_approximation_sweep.csv",index=False)
rows.append(["E12","large-warp approximation","worst max relative error in sweep",float(sweep_df.max_relative_error.max()),len(sweep_df)])
rows.append(["E12","large-warp approximation","c=0.4,kappa=10 max relative error",float(sweep_df[(sweep_df.c==0.4)&(sweep_df.kappa==10)].max_relative_error.iloc[0]),4])

# E13 source Table A.1 numerical audit
listed=np.array([3.52,6.71,9.88]); true09=bessel_zeros(0.9,3); true08=bessel_zeros(0.8,3)
audit=pd.DataFrame({"mode":[1,2,3],"source_value":listed,"J_0.9_zero":true09,"relative_error_vs_J0.9":(listed-true09)/true09,"J_0.8_zero":true08,"relative_error_vs_J0.8":(listed-true08)/true08})
audit.to_csv(RES/"final_source_table_A1_audit.csv",index=False)
rows.append(["E13","source table audit","max absolute relative error vs stated J_0.9",float(np.max(np.abs((listed-true09)/true09))),3])
rows.append(["E13","source table audit","max absolute relative error vs J_0.8",float(np.max(np.abs((listed-true08)/true08))),3])

# E14 three-generation spacing stress test
cs=np.linspace(-0.49,2.0,500)
gen=[]
for c in cs:
    nu=c+0.5; z=bessel_zeros(nu,3); gen.append([c,nu,z[1]/z[0],z[2]/z[0]])
gen_df=pd.DataFrame(gen,columns=["c","nu","x2_over_x1","x3_over_x1"])
# 2026 PDG values (MeV)
me=0.51099895069; mmu=105.6583755; mtau=1776.93
obs2=mmu/me; obs3=mtau/me
gen_df["muon_electron_ratio_PDG2026"]=obs2; gen_df["tau_electron_ratio_PDG2026"]=obs3
gen_df.to_csv(RES/"final_generation_spacing_scan.csv",index=False)
rows.append(["E14","generation spacing","max x2/x1 over c scan",float(gen_df.x2_over_x1.max()),len(gen_df)])
rows.append(["E14","generation spacing","max x3/x1 over c scan",float(gen_df.x3_over_x1.max()),len(gen_df)])
rows.append(["E14","generation spacing","PDG2026 mu/e mass ratio",obs2,1])
rows.append(["E14","generation spacing","PDG2026 tau/e mass ratio",obs3,1])

summary=pd.DataFrame(rows,columns=["experiment","family","metric","estimate","replicates_or_n"])
summary.to_csv(RES/"all_experiments_summary.csv",index=False)

# ---------- Figures ----------
plt.figure(figsize=(6.4,4.3))
plt.loglog(conv_df.grid_N,conv_df.max_relative_error,marker='o')
plt.xlabel('Interior finite-difference grid points N')
plt.ylabel('Maximum relative error, first six modes')
plt.title('Second-order convergence of warped spectral discretization')
plt.tight_layout(); plt.savefig(FIG/'fig1_fd_convergence.png',dpi=240); plt.close()

plt.figure(figsize=(6.5,4.3))
for c in [-0.4,0.0,0.4,0.8,1.2]:
    d=sweep_df[sweep_df.c==c]
    plt.semilogy(d.kappa,d.max_relative_error,marker='o',label=f'c={c:g}')
plt.xlabel('Warp modulus kL')
plt.ylabel('Max relative error vs J_nu zeros (modes 1-4)')
plt.title('Non-uniform validity of the large-warp Bessel approximation')
plt.legend(); plt.tight_layout(); plt.savefig(FIG/'fig2_bessel_approximation.png',dpi=240); plt.close()

plt.figure(figsize=(6.4,4.3))
plt.plot(audit['mode'],100*np.abs(audit['relative_error_vs_J0.9']),marker='o',label='Error vs stated J_0.9')
plt.plot(audit['mode'],100*np.abs(audit['relative_error_vs_J0.8']),marker='o',label='Error vs J_0.8')
plt.xlabel('Mode n'); plt.ylabel('Absolute relative error (%)')
plt.title('Numerical audit of original OFT Table A.1')
plt.legend(); plt.tight_layout(); plt.savefig(FIG/'fig3_source_table_audit.png',dpi=240); plt.close()

plt.figure(figsize=(6.5,4.3))
plt.plot(gen_df.c,gen_df.x2_over_x1,label='KK x2/x1')
plt.plot(gen_df.c,gen_df.x3_over_x1,label='KK x3/x1')
plt.axhline(obs2,linestyle='--',label='PDG mu/e')
plt.axhline(obs3,linestyle=':',label='PDG tau/e')
plt.yscale('log'); plt.xlabel('Bulk mass modulus c'); plt.ylabel('Mass / first-mode mass')
plt.title('Pure KK spacing cannot reproduce charged-lepton hierarchy')
plt.legend(); plt.tight_layout(); plt.savefig(FIG/'fig4_generation_spacing.png',dpi=240); plt.close()

plt.figure(figsize=(6.4,4.3))
mask=disc_df.mu>0
plt.loglog(disc_df.loc[mask,'mu'],disc_df.loc[mask,'discriminant'],marker='o')
plt.xlabel('|mu|'); plt.ylabel('Spectral discriminant')
plt.title('Critical-locus scaling')
plt.tight_layout(); plt.savefig(FIG/'fig5_discriminant.png',dpi=240); plt.close()

plt.figure(figsize=(7.2,4.6))
plt.bar(abr_df.ablation,abr_df.reconstructibility_score)
plt.ylabel('Normalized reconstructibility score')
plt.title('Invariant-family ablation')
plt.xticks(rotation=40,ha='right'); plt.tight_layout(); plt.savefig(FIG/'fig6_reconstructibility.png',dpi=240); plt.close()

# Machine-readable run metadata + hashes
meta={"seed":SEED,"python_protocol":"OFT invariant synthetic/continuum validation v3","n_experiments":14,"files":{}}
for p in sorted(list(RES.glob('*.csv'))+list(FIG.glob('*.png'))):
    meta['files'][str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
(ROOT/'results'/'run_manifest.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
print(summary.to_string(index=False))
print(f"\nWrote results to {RES} and figures to {FIG}")
