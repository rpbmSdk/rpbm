let { text, createBlock, list, multi, html, toggler, comment } = bdom;
  let { makeRefWrapper, prepareList, OwlError, withKey, markRaw } = helpers;
  // Template name: "rpbm_agent.AgentWidgetDialog"
  const comp1 = app.createComponent(`VehiculeComponent`, true, false, false, ["vehicule","selectedVehiculeId"]);
  const comp2 = app.createComponent(`Dialog`, true, true, false, []);
  
  let block2 = createBlock(`<button class="btn btn-primary" block-handler-0="click"> Confirmer </button>`);
  let block3 = createBlock(`<button class="btn btn-secondary" block-handler-0="click"> Annuler </button>`);
  let block5 = createBlock(`<input class="o_input" id="immatriculation" placeholder="Immatriculation" style="text-transform: uppercase;" block-handler-0="change" block-ref="1"/>`);
  let block6 = createBlock(`<button class="btn btn-primary" block-handler-0="click"> Rechercher </button>`);
  let block10 = createBlock(`<button class="btn btn-primary" block-handler-0="click"> getPlanche </button>`);
  let block11 = createBlock(`<div><block-child-0/><block-child-1/><block-child-2/></div>`);
  let block13 = createBlock(`<button block-attribute-0="class" block-handler-1="click"><block-text-2/></button>`);
  let block14 = createBlock(`<button class="btn btn-primary" block-handler-0="click"> getPieces </button>`);
  let block15 = createBlock(`<div class="d-flex justify-content-between"><block-child-0/></div>`);
  let block17 = createBlock(`<div class="card" style="width: 18rem; display: inline-block; margin: 10px;" block-attribute-0="data-piece-id" block-handler-1="click.prevent"><div class="card-body"><h5 class="card-title"><block-text-2/></h5></div></div>`);
  
  function slot1(ctx, node, key = "") {
    let hdlr1 = [ctx['onConfirm'], ctx];
    const b2 = block2([hdlr1]);
    let hdlr2 = [ctx['onDiscard'], ctx];
    const b3 = block3([hdlr2]);
    return multi([b2, b3]);
  }
  
  function slot2(ctx, node, key = "") {
    let refWrapper = makeRefWrapper(this.__owl__);
    let b5, b6, b7;
    let hdlr3 = [ctx['onChangeImmatriculation'], ctx];
    let ref1 = refWrapper(`immatriculation`, (el) => this.__owl__.setRef((`immatriculation`), el));
    b5 = block5([hdlr3, ref1]);
    let hdlr4 = [ctx['onSearchImmatriculation'], ctx];
    b6 = block6([hdlr4]);
    if (ctx['vehicules'].length>0) {
      let b8, b10, b11;
      ctx = Object.create(ctx);
      const [k_block8, v_block8, l_block8, c_block8] = prepareList(ctx['vehicules']);;
      const keys8 = new Set();
      for (let i1 = 0; i1 < l_block8; i1++) {
        ctx[`vehicule`] = k_block8[i1];
        const key1 = ctx['vehicule'].id;
        if (keys8.has(String(key1))) { throw new OwlError(`Got duplicate key in t-foreach: ${key1}`)}
        keys8.add(String(key1));
        const props1 = {vehicule: ctx['vehicule'],selectedVehiculeId: ctx['selectedVehiculeId']};
        helpers.validateProps(`VehiculeComponent`, props1, this);
        c_block8[i1] = withKey(comp1(props1, key + `__1__${key1}`, node, this, null), key1);
      }
      ctx = ctx.__proto__;
      b8 = list(c_block8);
      if (ctx['selectedVehicule']) {
        let hdlr5 = [ctx['getPlanche'], ctx];
        b10 = block10([hdlr5]);
      }
      if (ctx['planche']) {
        let b12, b14, b15;
        ctx = Object.create(ctx);
        const [k_block12, v_block12, l_block12, c_block12] = prepareList(ctx['calques']);;
        const keys12 = new Set();
        for (let i1 = 0; i1 < l_block12; i1++) {
          ctx[`calque`] = k_block12[i1];
          const key1 = ctx['calque'].id;
          if (keys12.has(String(key1))) { throw new OwlError(`Got duplicate key in t-foreach: ${key1}`)}
          keys12.add(String(key1));
          let attr1 = ctx['btn']ctx['btn']-ctx['primary'];
          const v1 = ctx['this'];
          const v2 = ctx['calque'];
          let hdlr6 = [()=>v1.onClickCalque(v2.id), ctx];
          let txt1 = ctx['calque'].libelle;
          c_block12[i1] = withKey(block13([attr1, hdlr6, txt1]), key1);
        }
        ctx = ctx.__proto__;
        b12 = list(c_block12);
        if (ctx['selectedCalque']) {
          let hdlr7 = [ctx['getPieces'], ctx];
          b14 = block14([hdlr7]);
        }
        if (ctx['pieces'].length>0) {
          ctx = Object.create(ctx);
          const [k_block16, v_block16, l_block16, c_block16] = prepareList(ctx['pieces']);;
          const keys16 = new Set();
          for (let i1 = 0; i1 < l_block16; i1++) {
            ctx[`piece`] = k_block16[i1];
            const key1 = ctx['piece'].id;
            if (keys16.has(String(key1))) { throw new OwlError(`Got duplicate key in t-foreach: ${key1}`)}
            keys16.add(String(key1));
            let attr2 = ctx['piece'].id;
            let hdlr8 = ["prevent", ctx['onSelectPiece'](ctx['piece'].id), ctx];
            let txt2 = ctx['piece'].libelle;
            c_block16[i1] = withKey(block17([attr2, hdlr8, txt2]), key1);
          }
          ctx = ctx.__proto__;
          const b16 = list(c_block16);
          b15 = block15([], [b16]);
        }
        b11 = block11([], [b12, b14, b15]);
      }
      b7 = multi([b8, b10, b11]);
    }
    return multi([b5, b6, b7]);
  }
  
  return function template(ctx, node, key = "") {
    const props2 = {slots: markRaw({'footer': {__render: slot1.bind(this), __ctx: ctx}, 'default': {__render: slot2.bind(this), __ctx: ctx}})};
    helpers.validateProps(`Dialog`, props2, this);
    return comp2(props2, key + `__2`, node, this, null);
  }